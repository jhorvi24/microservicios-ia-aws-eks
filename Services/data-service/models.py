from database import db
from datetime import datetime, timezone

class SentimentResult(db.Model):
    __tablename__ = "sentiment_results"

    id         = db.Column(db.Integer, primary_key=True)
    text       = db.Column(db.Text, nullable=False)
    label      = db.Column(db.String(20))       # POSITIVE / NEGATIVE / NEUTRAL
    score      = db.Column(db.Float)            # confianza del modelo (0.0 - 1.0)
    source     = db.Column(db.String(50), default="dashboard")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id":         self.id,
            "text":       self.text,
            "label":      self.label,
            "score":      self.score,
            "source":     self.source,
            "created_at": self.created_at.isoformat()
        }