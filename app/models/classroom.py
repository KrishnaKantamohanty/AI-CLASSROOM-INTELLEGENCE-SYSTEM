"""Classroom model — physical classroom information and capacity."""
from datetime import datetime
from app.extensions import db


class Classroom(db.Model):
    __tablename__ = 'classrooms'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    building = db.Column(db.String(100), default='Main Building')
    floor = db.Column(db.Integer, default=1)
    capacity = db.Column(db.Integer, nullable=False, default=60)
    current_occupancy = db.Column(db.Integer, default=0)
    has_camera = db.Column(db.Boolean, default=False)
    camera_url = db.Column(db.String(256))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    attendance_records = db.relationship('Attendance', backref='classroom', lazy='dynamic')

    @property
    def occupancy_percentage(self):
        if self.capacity == 0:
            return 0
        return round((self.current_occupancy / self.capacity) * 100, 1)

    def __repr__(self):
        return f'<Classroom {self.name} ({self.current_occupancy}/{self.capacity})>'
