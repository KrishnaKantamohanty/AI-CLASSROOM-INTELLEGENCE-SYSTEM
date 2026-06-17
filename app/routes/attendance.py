"""Attendance management routes."""
from datetime import date, datetime
import os
import uuid
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from werkzeug.utils import secure_filename
from flask_login import login_required
from app.extensions import db
from app.models.attendance import Attendance
from app.models.student import Student
from app.services.attendance_service import AttendanceService
from app.services.face_recognition_service import FaceRecognitionService

attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')


@attendance_bp.route('/')
@login_required
def index():
    """View attendance records."""
    selected_date = request.args.get('date', date.today().isoformat())
    try:
        filter_date = date.fromisoformat(selected_date)
    except ValueError:
        filter_date = date.today()

    records = db.session.query(Attendance, Student).join(
        Student, Attendance.student_id == Student.id
    ).filter(
        Attendance.date == filter_date
    ).order_by(Student.roll_number).all()

    stats = AttendanceService.get_today_stats()

    return render_template('attendance/index.html',
                           records=records,
                           selected_date=filter_date,
                           stats=stats)


@attendance_bp.route('/mark', methods=['POST'])
@login_required
def mark_attendance():
    """Mark attendance for a student."""
    student_id = request.form.get('student_id', type=int)
    status = request.form.get('status', 'present')
    att_date = request.form.get('date', date.today().isoformat())

    try:
        att_date = date.fromisoformat(att_date)
    except ValueError:
        att_date = date.today()

    if not student_id:
        flash('Invalid student.', 'danger')
        return redirect(url_for('attendance.index'))

    # Check if record already exists
    existing = Attendance.query.filter_by(student_id=student_id, date=att_date).first()
    if existing:
        existing.status = status
        if status in ('present', 'late'):
            existing.time_in = datetime.now().time()
        flash('Attendance updated.', 'success')
    else:
        record = Attendance(
            student_id=student_id,
            date=att_date,
            status=status,
            time_in=datetime.now().time() if status in ('present', 'late') else None,
            detected_by='manual'
        )
        db.session.add(record)
        flash('Attendance marked.', 'success')

    db.session.commit()
    return redirect(url_for('attendance.index', date=att_date.isoformat()))


@attendance_bp.route('/bulk', methods=['POST'])
@login_required
def bulk_mark():
    """Mark attendance for all students at once."""
    att_date = request.form.get('date', date.today().isoformat())
    try:
        att_date = date.fromisoformat(att_date)
    except ValueError:
        att_date = date.today()

    students = Student.query.filter_by(is_active=True).all()
    count = 0

    for student in students:
        status = request.form.get(f'status_{student.id}', 'absent')
        existing = Attendance.query.filter_by(student_id=student.id, date=att_date).first()
        if existing:
            existing.status = status
            if status in ('present', 'late'):
                existing.time_in = datetime.now().time()
        else:
            record = Attendance(
                student_id=student.id,
                date=att_date,
                status=status,
                time_in=datetime.now().time() if status in ('present', 'late') else None,
                detected_by='manual'
            )
            db.session.add(record)
        count += 1

    db.session.commit()
    flash(f'Attendance marked for {count} students.', 'success')
    return redirect(url_for('attendance.index', date=att_date.isoformat()))


@attendance_bp.route('/upload', methods=['POST'])
@login_required
def upload_image():
    """Process an uploaded classroom photo for attendance."""
    if 'classroom_photo' not in request.files:
        flash('No file part uploaded.', 'danger')
        return redirect(url_for('attendance.index'))

    file = request.files['classroom_photo']
    if file.filename == '':
        flash('No file selected.', 'warning')
        return redirect(url_for('attendance.index'))

    # Check extension
    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif'}):
        flash('Invalid file format. Please upload an image (JPG, PNG).', 'danger')
        return redirect(url_for('attendance.index'))

    # Ensure temp dir exists
    temp_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads/students'), 'temp')
    os.makedirs(temp_dir, exist_ok=True)

    # Save temp file
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"scan_{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(temp_dir, filename)
    file.save(filepath)

    # Process image
    recognized_students, face_count = FaceRecognitionService.process_classroom_image(filepath)

    # Cleanup temp file
    try:
        os.remove(filepath)
    except OSError:
        pass

    if face_count == 0:
        flash('No faces detected in the image. Please try a clearer photo.', 'warning')
        return redirect(url_for('attendance.index'))

    # Mark attendance for recognized students
    today = date.today()
    marked_names = []
    
    for student in recognized_students:
        existing = Attendance.query.filter_by(student_id=student.id, date=today).first()
        if existing:
            if existing.status == 'absent':
                existing.status = 'present'
                existing.time_in = datetime.now().time()
        else:
            record = Attendance(
                student_id=student.id,
                date=today,
                status='present',
                time_in=datetime.now().time(),
                detected_by='ai_detection'
            )
            db.session.add(record)
        marked_names.append(student.name)

    db.session.commit()
    
    # Generate success message
    names_str = ", ".join(marked_names)
    flash(f'Success! Detected {face_count} faces. Marked present: {names_str}', 'success')
    
    return redirect(url_for('attendance.index'))
