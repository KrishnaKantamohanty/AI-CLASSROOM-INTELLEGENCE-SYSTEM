"""Report model — metadata for generated reports."""
from datetime import datetime
from app.extensions import db


class Report(db.Model):
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    report_type = db.Column(db.String(30), nullable=False)  # daily, weekly, monthly, semester
    file_format = db.Column(db.String(10), nullable=False)  # pdf, excel, csv
    file_path = db.Column(db.String(500))
    generated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    period_start = db.Column(db.Date)
    period_end = db.Column(db.Date)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    author = db.relationship('User', backref='reports')

    def __repr__(self):
        return f'<Report {self.title} ({self.report_type})>'
