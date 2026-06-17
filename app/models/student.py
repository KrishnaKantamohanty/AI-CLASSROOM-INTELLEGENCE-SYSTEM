"""Student model — student profiles and academic information."""
from datetime import datetime
from app.extensions import db


class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    department = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.Integer, nullable=False, default=1)
    section = db.Column(db.String(10), default='A')
    photo_path = db.Column(db.String(256))
    gender = db.Column(db.String(10), default='Other')
    date_of_birth = db.Column(db.Date)
    guardian_name = db.Column(db.String(100))
    guardian_phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    risk_status = db.Column(db.String(20), default='normal')  # normal, at_risk, critical
    is_active = db.Column(db.Boolean, default=True)
    enrolled_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    attendance_records = db.relationship('Attendance', backref='student', lazy='dynamic')

    @property
    def attendance_percentage(self):
        """Calculate overall attendance percentage."""
        total = self.attendance_records.count()
        if total == 0:
            return 0.0
        present = self.attendance_records.filter_by(status='present').count()
        late = self.attendance_records.filter_by(status='late').count()
        return round(((present + late) / total) * 100, 1)

    @property
    def risk_level(self):
        """Determine risk level based on attendance."""
        pct = self.attendance_percentage
        if pct >= 75:
            return 'normal'
        elif pct >= 50:
            return 'at_risk'
        else:
            return 'critical'

    def __repr__(self):
        return f'<Student {self.roll_number}: {self.name}>'
