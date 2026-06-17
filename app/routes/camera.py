"""QR Attendance Session routes — teacher displays QR, students scan."""
import socket
from datetime import date, datetime
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.student import Student
from app.models.attendance import Attendance
from app.models.attendance_session import AttendanceSession

camera_bp = Blueprint('camera', __name__, url_prefix='/camera')


def _get_server_ip():
    """Get the LAN IP address of this machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'


@camera_bp.route('/')
@login_required
def index():
    """QR Attendance Session dashboard for teachers."""
    # Get active session if any
    active_session = AttendanceSession.query.filter_by(
        created_by=current_user.id,
        is_active=True
    ).order_by(AttendanceSession.created_at.desc()).first()

    # Deactivate if expired
    if active_session and active_session.is_expired:
        active_session.is_active = False
        db.session.commit()
        active_session = None

    server_ip = _get_server_ip()

    return render_template('camera/index.html',
                           active_session=active_session,
                           server_ip=server_ip)


@camera_bp.route('/generate', methods=['POST'])
@login_required
def generate_session():
    """Create a new QR attendance session."""
    duration = request.form.get('duration', 5, type=int)
    description = request.form.get('description', '').strip()

    # Clamp duration between 1 and 30 minutes
    duration = max(1, min(30, duration))

    # Deactivate any existing active sessions by this user
    old_sessions = AttendanceSession.query.filter_by(
        created_by=current_user.id,
        is_active=True
    ).all()
    for s in old_sessions:
        s.is_active = False
    db.session.commit()

    # Create new session
    session = AttendanceSession.create_session(
        user_id=current_user.id,
        duration_minutes=duration,
        description=description
    )

    server_ip = _get_server_ip()
    checkin_url = f'http://{server_ip}:5000/checkin/{session.token}'

    return jsonify({
        'success': True,
        'token': session.token,
        'checkin_url': checkin_url,
        'expires_at': session.expires_at.isoformat(),
        'seconds_remaining': session.seconds_remaining,
        'description': session.description
    })


@camera_bp.route('/session-status')
@login_required
def session_status():
    """Poll endpoint for live session info and recent check-ins."""
    active_session = AttendanceSession.query.filter_by(
        created_by=current_user.id,
        is_active=True
    ).order_by(AttendanceSession.created_at.desc()).first()

    if not active_session:
        return jsonify({'active': False, 'checkins': [], 'count': 0})

    if active_session.is_expired:
        active_session.is_active = False
        db.session.commit()
        return jsonify({'active': False, 'expired': True, 'checkins': [], 'count': 0})

    # Get check-ins for this session
    checkins = (
        Attendance.query
        .filter_by(session_id=active_session.id)
        .join(Student)
        .order_by(Attendance.created_at.desc())
        .limit(50)
        .all()
    )

    checkin_list = [{
        'student_name': c.student.name,
        'roll_number': c.student.roll_number,
        'time': c.time_in.strftime('%H:%M:%S') if c.time_in else '--:--:--',
        'department': c.student.department
    } for c in checkins]

    today = date.today()
    total_today = Attendance.query.filter_by(date=today).filter(
        Attendance.status.in_(['present', 'late'])
    ).count()
    total_students = Student.query.filter_by(is_active=True).count()

    return jsonify({
        'active': True,
        'seconds_remaining': active_session.seconds_remaining,
        'session_count': len(checkin_list),
        'total_today': total_today,
        'total_students': total_students,
        'checkins': checkin_list
    })


@camera_bp.route('/stop', methods=['POST'])
@login_required
def stop_session():
    """Manually stop the active session."""
    sessions = AttendanceSession.query.filter_by(
        created_by=current_user.id,
        is_active=True
    ).all()
    for s in sessions:
        s.is_active = False
    db.session.commit()
    return jsonify({'success': True})
