#Model for sentiment analysis using DistilBERT

from flask import Flask, request, jsonify
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import requests
import torch
import os



app = Flask(__name__)

model_name = "distilbert-base-uncased-finetuned-sst-2-english"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

model.eval()

BD_SERVICE_URL = os.getenv("BD_SERVICE_URL", "http://localhost:8001")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)


def preprocess(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    return inputs

def predict_sentiment(text):
    inputs = preprocess(text)
    inputs = {k: v.to(device) for k, v in inputs.items()}  # mover al device correcto

    with torch.no_grad():  # más eficiente en inferencia
        outputs = model(**inputs)
    
    logits = outputs.logits
    probabilities = torch.softmax(logits, dim=-1)
    predicted_class = torch.argmax(logits, axis=-1).item()
    confidence = probabilities[0][predicted_class].item()  # valor entre 0 y 1

    sentiment = "positive" if predicted_class == 1 else "negative"

    return sentiment, confidence


def save_sentiment(text: str, label: str, score: float):
    payload = {
        "text":   text,
        "label":  label,
        "score":  score,
        "source": "distilbert-service"
    }
    try:
        response = requests.post(f"{BD_SERVICE_URL}/results", json=payload, timeout=30)
        print(f"Saving result: {payload}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error saving result: {e}")
        return None  
    

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"message": "Service is healthy"}), 200


@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    text = data.get('text', '')

    sentiment, confidence = predict_sentiment(text)   

    save_sentiment(text, sentiment, confidence)

    return jsonify({
        "sentiment": sentiment,
        "confidence": round(confidence,4)
    }),200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

