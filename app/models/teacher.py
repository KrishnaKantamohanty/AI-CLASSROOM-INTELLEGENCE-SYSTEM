"""Teacher model."""
from datetime import datetime
from app.extensions import db


class Teacher(db.Model):
    __tablename__ = 'teachers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    employee_id = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    department = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(100))
    qualification = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Teacher {self.employee_id}: {self.name}>'
