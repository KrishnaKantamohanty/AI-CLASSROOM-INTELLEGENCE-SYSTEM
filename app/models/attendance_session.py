"""AttendanceSession model — time-limited QR attendance sessions."""
import uuid
from datetime import datetime, timedelta
from app.extensions import db


class AttendanceSession(db.Model):
    __tablename__ = 'attendance_sessions'

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True,
                      default=lambda: uuid.uuid4().hex)
    description = db.Column(db.String(200), default='')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    creator = db.relationship('User', backref='attendance_sessions')
    checkins = db.relationship('Attendance', backref='session', lazy='dynamic')

    @staticmethod
    def create_session(user_id, duration_minutes=5, description=''):
        """Create a new attendance session with a unique token."""
        now = datetime.utcnow()
        session = AttendanceSession(
            created_by=user_id,
            description=description,
            expires_at=now + timedelta(minutes=duration_minutes)
        )
        db.session.add(session)
        db.session.commit()
        return session

    @property
    def is_expired(self):
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self):
        return self.is_active and not self.is_expired

    @property
    def seconds_remaining(self):
        delta = self.expires_at - datetime.utcnow()
        return max(0, int(delta.total_seconds()))

    def __repr__(self):
        return f'<AttendanceSession {self.token[:8]}... expires={self.expires_at}>'
