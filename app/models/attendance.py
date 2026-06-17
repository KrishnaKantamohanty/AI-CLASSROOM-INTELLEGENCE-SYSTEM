"""Attendance model — daily attendance records."""
from datetime import datetime, date
from app.extensions import db


class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'), nullable=True)
    date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    time_in = db.Column(db.Time)
    time_out = db.Column(db.Time)
    status = db.Column(db.String(10), nullable=False, default='absent')  # present, absent, late
    detected_by = db.Column(db.String(20), default='manual')  # manual, ai_detection, face_recognition
    confidence = db.Column(db.Float, default=1.0)
    notes = db.Column(db.Text)
    session_id = db.Column(db.Integer, db.ForeignKey('attendance_sessions.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Composite unique constraint: one record per student per day
    __table_args__ = (
        db.UniqueConstraint('student_id', 'date', name='uq_student_date'),
    )

    def __repr__(self):
        return f'<Attendance {self.student_id} {self.date}: {self.status}>'
