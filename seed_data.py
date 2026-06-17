"""Database Seeding Script.
Populates the database with sample students, teachers, and attendance records
for testing and demonstration purposes.
"""
import os
import random
from datetime import date, timedelta
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.classroom import Classroom
from app.models.attendance import Attendance

app = create_app()

def seed_database():
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()
        print("Database tables created.")

        # 1. Create Users
        admin = User(username='admin', email='admin@school.edu', role='admin', first_name='System', last_name='Admin')
        admin.set_password('admin123')
        db.session.add(admin)

        teacher = User(username='teacher', email='teacher@school.edu', role='teacher', first_name='John', last_name='Doe')
        teacher.set_password('teacher123')
        db.session.add(teacher)

        print("Users created.")

        # 2. Create Classroom
        room = Classroom(name='Room 101', capacity=60, building='Main Building', floor=1, has_camera=True)
        db.session.add(room)
        print("Classroom created.")

        # 3. Create Students (50 students)
        departments = ['Computer Science', 'Electronics', 'Mechanical', 'Civil']
        first_names = ['James', 'Mary', 'Robert', 'Patricia', 'John', 'Jennifer', 'Michael', 'Linda', 'David', 'Elizabeth', 'William', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica', 'Thomas', 'Sarah', 'Charles', 'Karen']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin']

        students = []
        for i in range(50):
            # Create a mix of regular and irregular students
            student_type = random.choices(['regular', 'average', 'poor'], weights=[0.6, 0.3, 0.1])[0]

            s = Student(
                name=f"{random.choice(first_names)} {random.choice(last_names)}",
                roll_number=f"CS{2024001+i:03d}",
                email=f"student{i}@school.edu",
                department=random.choice(departments),
                semester=random.randint(1, 8),
                section=random.choice(['A', 'B'])
            )
            # Store type for attendance generation
            s._type = student_type
            db.session.add(s)
            students.append(s)

        db.session.commit() # Commit to get student IDs
        print(f"{len(students)} Students created.")

        # 4. Generate Attendance History (Last 30 days)
        today = date.today()
        history_days = 30
        attendance_records = []

        for day_offset in range(history_days):
            current_date = today - timedelta(days=history_days - 1 - day_offset)
            # Skip weekends (Sunday=6)
            if current_date.weekday() == 6:
                continue

            for s in students:
                # Determine attendance probability based on student type
                if s._type == 'regular':
                    prob = 0.95
                elif s._type == 'average':
                    prob = 0.75
                else:
                    prob = 0.40

                if random.random() < prob:
                    status = 'present' if random.random() > 0.1 else 'late'
                    from datetime import time
                    h = 8 if status == 'present' else random.randint(8, 9)
                    m = random.randint(0, 59)
                    time_in = time(h, m)
                else:
                    status = 'absent'
                    time_in = None

                record = Attendance(
                    student_id=s.id,
                    classroom_id=room.id,
                    date=current_date,
                    status=status,
                    time_in=time_in,
                    detected_by=random.choice(['ai_detection', 'manual'])
                )
                attendance_records.append(record)

        db.session.add_all(attendance_records)
        db.session.commit()
        print(f"{len(attendance_records)} Attendance records created.")
        print("Database seeding completed successfully.")
        print("You can log in with username 'admin' and password 'admin123'.")

if __name__ == '__main__':
    seed_database()
