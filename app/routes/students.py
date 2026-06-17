"""Student management routes — CRUD operations."""
import os
import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user
from app.extensions import db
from app.models.student import Student
from app.services.attendance_service import AttendanceService
from app.models.attendance import Attendance
from app.services.prediction_service import PredictionService

students_bp = Blueprint('students', __name__, url_prefix='/students')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def handle_photo_upload(file, student_id):
    """Saves photo and returns the filename."""
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        # Create a unique, secure filename
        filename = f"{student_id}_{uuid.uuid4().hex[:8]}.{ext}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return filename
    return None

@students_bp.route('/')
@login_required
def list_students():
    """List all students with search and filter."""
    search = request.args.get('search', '').strip()
    department = request.args.get('department', '').strip()
    risk = request.args.get('risk', '').strip()
    page = request.args.get('page', 1, type=int)

    query = Student.query.filter_by(is_active=True)

    if search:
        query = query.filter(
            db.or_(
                Student.name.ilike(f'%{search}%'),
                Student.roll_number.ilike(f'%{search}%'),
                Student.email.ilike(f'%{search}%')
            )
        )
    if department:
        query = query.filter_by(department=department)

    students = query.order_by(Student.name).paginate(page=page, per_page=20, error_out=False)

    # Get unique departments for filter dropdown
    departments = db.session.query(Student.department).distinct().order_by(Student.department).all()
    departments = [d[0] for d in departments]

    return render_template('students/list.html',
                           students=students,
                           departments=departments,
                           search=search,
                           selected_department=department)


@students_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_student():
    """Add a new student."""
    if request.method == 'POST':
        student = Student(
            name=request.form.get('name', '').strip(),
            roll_number=request.form.get('roll_number', '').strip(),
            email=request.form.get('email', '').strip(),
            phone=request.form.get('phone', '').strip(),
            department=request.form.get('department', '').strip(),
            semester=int(request.form.get('semester', 1)),
            section=request.form.get('section', 'A').strip(),
            gender=request.form.get('gender', 'Other'),
            guardian_name=request.form.get('guardian_name', '').strip(),
            guardian_phone=request.form.get('guardian_phone', '').strip(),
            address=request.form.get('address', '').strip()
        )

        if Student.query.filter_by(roll_number=student.roll_number).first():
            flash('A student with this roll number already exists.', 'danger')
            return render_template('students/form.html', student=None, action='Add')

        db.session.add(student)
        db.session.flush()  # To get the student.id before commit

        # Handle photo upload
        if 'photo' in request.files:
            file = request.files['photo']
            if file.filename != '':
                filename = handle_photo_upload(file, student.id)
                if filename:
                    student.photo_path = filename

        db.session.commit()
        flash(f'Student {student.name} added successfully!', 'success')
        return redirect(url_for('students.list_students'))

    return render_template('students/form.html', student=None, action='Add')


@students_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_student(id):
    """Edit an existing student."""
    student = Student.query.get_or_404(id)

    if request.method == 'POST':
        student.name = request.form.get('name', '').strip()
        student.email = request.form.get('email', '').strip()
        student.phone = request.form.get('phone', '').strip()
        student.department = request.form.get('department', '').strip()
        student.semester = int(request.form.get('semester', 1))
        student.section = request.form.get('section', 'A').strip()
        student.gender = request.form.get('gender', 'Other')
        student.guardian_name = request.form.get('guardian_name', '').strip()
        student.guardian_phone = request.form.get('guardian_phone', '').strip()
        student.address = request.form.get('address', '').strip()

        # Handle photo upload
        if 'photo' in request.files:
            file = request.files['photo']
            if file.filename != '':
                filename = handle_photo_upload(file, student.id)
                if filename:
                    # Delete old photo if exists
                    if student.photo_path:
                        old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], student.photo_path)
                        if os.path.exists(old_path):
                            try:
                                os.remove(old_path)
                            except OSError:
                                pass
                    student.photo_path = filename

        db.session.commit()
        flash(f'Student {student.name} updated successfully!', 'success')
        return redirect(url_for('students.profile', id=student.id))

    return render_template('students/form.html', student=student, action='Edit')


@students_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_student(id):
    """Soft-delete a student."""
    student = Student.query.get_or_404(id)
    student.is_active = False
    db.session.commit()
    flash(f'Student {student.name} has been removed.', 'info')
    return redirect(url_for('students.list_students'))


@students_bp.route('/profile/<int:id>')
@login_required
def profile(id):
    """View student profile with analytics."""
    student = Student.query.get_or_404(id)
    prediction = PredictionService.predict_student_absence(student.id)

    recent_records = Attendance.query.filter_by(student_id=student.id).order_by(Attendance.date.desc()).limit(15).all()

    return render_template('students/profile.html',
                           student=student,
                           prediction=prediction,
                           recent_records=recent_records)

