"""AI Insight model — stores AI-generated insights and recommendations."""
from datetime import datetime
from app.extensions import db


class AIInsight(db.Model):
    __tablename__ = 'ai_insights'

    id = db.Column(db.Integer, primary_key=True)
    insight_text = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # attendance, occupancy, risk, performance, engagement
    severity = db.Column(db.String(20), default='info')  # info, warning, critical, success
    icon = db.Column(db.String(50), default='bi-lightbulb')
    is_read = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'<AIInsight [{self.severity}] {self.insight_text[:50]}>'
