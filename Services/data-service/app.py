from flask import Flask, request, jsonify
from database import db
from models import SentimentResult
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

DB_URL = os.getenv("DATABASE_URL", "sqlite:///sentiments.db")
print(f"Database URL: {DB_URL}")

app.config["SQLALCHEMY_DATABASE_URI"] = DB_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()  # Crea las tablas si no existen



@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "Ok"}), 200

# Guardar resultado
@app.route("/results", methods=["POST"])
def save_result():
    data = request.get_json()
    record = SentimentResult(
        text   = data["text"],
        label  = data["label"],
        score  = data["score"],
        source = data.get("source", "distilbert-service")
    )
    db.session.add(record)
    db.session.commit()
    return jsonify(record.to_dict()), 201


# Obtener todos los resultados
@app.route("/results", methods=["GET"])
def get_results():
    skip  = request.args.get("skip", 0, type=int)
    limit = request.args.get("limit", 100, type=int)
    records = SentimentResult.query.offset(skip).limit(limit).all()
    return jsonify([r.to_dict() for r in records])


# Obtener por ID
@app.route("/results/<int:result_id>", methods=["GET"])
def get_result(result_id):
    record = SentimentResult.query.get(result_id)
    if not record:
        return jsonify({"error": "Not found"}), 404
    return jsonify(record.to_dict())


# Estadísticas para el dashboard
@app.route("/stats", methods=["GET"])
def get_stats():
    total     = SentimentResult.query.count()
    positives = SentimentResult.query.filter_by(label="POSITIVE").count()
    negatives = SentimentResult.query.filter_by(label="NEGATIVE").count()
    return jsonify({
        "total":        total,
        "positive":     positives,
        "negative":     negatives,
        "positive_pct": round((positives / total) * 100, 2) if total > 0 else 0
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=True)