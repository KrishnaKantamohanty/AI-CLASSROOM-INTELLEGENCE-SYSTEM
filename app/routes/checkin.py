"""Public student check-in routes — no login required."""
from datetime import date, datetime
from flask import Blueprint, render_template, request, jsonify
from app.extensions import db
from app.models.student import Student
from app.models.attendance import Attendance
from app.models.attendance_session import AttendanceSession

checkin_bp = Blueprint('checkin', __name__, url_prefix='/checkin')


@checkin_bp.route('/<token>', methods=['GET'])
def checkin_page(token):
    """Render the mobile check-in form for a valid session."""
    session = AttendanceSession.query.filter_by(token=token).first()

    if not session or not session.is_valid:
        return render_template('checkin/expired.html'), 410

    return render_template('checkin/mobile.html', session=session)


@checkin_bp.route('/<token>/submit', methods=['POST'])
def checkin_submit(token):
    """Process a student check-in from the mobile form."""
    session = AttendanceSession.query.filter_by(token=token).first()

    if not session or not session.is_valid:
        return jsonify({'success': False, 'message': 'This session has expired. Please scan a new QR code.'}), 410

    roll_number = request.form.get('roll_number', '').strip().upper()

    if not roll_number:
        return jsonify({'success': False, 'message': 'Please enter your roll number.'}), 400

    student = Student.query.filter_by(roll_number=roll_number, is_active=True).first()
    if not student:
        return jsonify({'success': False, 'message': f'No student found with roll number "{roll_number}". Please check and try again.'}), 404

    today = date.today()
    now_time = datetime.now().time()

    # Check if already checked in today
    existing = Attendance.query.filter_by(student_id=student.id, date=today).first()

    if existing and existing.status in ('present', 'late'):
        return jsonify({
            'success': True,
            'already': True,
            'message': f'You are already checked in today, {student.name}!',
            'student_name': student.name,
            'roll_number': student.roll_number
        })

    if existing:
        # Update absent → present
        existing.status = 'present'
        existing.time_in = now_time
        existing.detected_by = 'qr_session'
        existing.session_id = session.id
    else:
        att = Attendance(
            student_id=student.id,
            date=today,
            time_in=now_time,
            status='present',
            detected_by='qr_session',
            session_id=session.id
        )
        db.session.add(att)

    db.session.commit()

    return jsonify({
        'success': True,
        'already': False,
        'message': f'Attendance marked! Welcome, {student.name}.',
        'student_name': student.name,
        'roll_number': student.roll_number
    })
