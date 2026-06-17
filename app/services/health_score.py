"""Health Score & Engagement Index — classroom performance metrics."""
from datetime import date, timedelta
from sqlalchemy import func
from app.extensions import db
from app.models.attendance import Attendance
from app.models.student import Student
from app.models.classroom import Classroom


class HealthScoreService:
    """Calculates Classroom Health Score and Engagement Index."""

    @staticmethod
    def get_classroom_health_score():
        """Calculate overall Classroom Health Score (0-100).

        Based on:
        - Attendance rate (40% weight)
        - Consistency / regularity (30% weight)
        - Classroom utilization (30% weight)
        """
        # Attendance component
        today = date.today()
        month_start = today.replace(day=1)

        total = Attendance.query.filter(Attendance.date >= month_start).count()
        present = Attendance.query.filter(
            Attendance.date >= month_start,
            Attendance.status.in_(['present', 'late'])
        ).count()
        attendance_rate = (present / total * 100) if total > 0 else 75

        # Consistency component: standard deviation of daily rates
        daily_results = db.session.query(
            Attendance.date,
            func.count(Attendance.id).label('total'),
            func.sum(
                db.case(
                    (Attendance.status.in_(['present', 'late']), 1),
                    else_=0
                )
            ).label('present')
        ).filter(
            Attendance.date >= month_start
        ).group_by(Attendance.date).all()

        daily_rates = []
        for r in daily_results:
            t = int(r.total or 0)
            p = int(r.present or 0)
            if t > 0:
                daily_rates.append(p / t * 100)

        if len(daily_rates) > 1:
            import numpy as np
            std = np.std(daily_rates)
            # Lower std = more consistent = higher score
            consistency_score = max(0, 100 - std * 3)
        else:
            consistency_score = 75

        # Utilization component
        classrooms = Classroom.query.filter_by(is_active=True).all()
        if classrooms:
            avg_util = sum(cr.occupancy_percentage for cr in classrooms) / len(classrooms)
        else:
            avg_util = 70

        # Weighted score
        health_score = (
            attendance_rate * 0.40 +
            consistency_score * 0.30 +
            avg_util * 0.30
        )

        health_score = round(min(100, max(0, health_score)), 1)

        if health_score >= 85:
            status = 'Excellent'
            color = 'success'
        elif health_score >= 70:
            status = 'Good'
            color = 'info'
        elif health_score >= 50:
            status = 'Needs Improvement'
            color = 'warning'
        else:
            status = 'Critical'
            color = 'danger'

        return {
            'score': health_score,
            'status': status,
            'color': color,
            'attendance_component': round(attendance_rate, 1),
            'consistency_component': round(consistency_score, 1),
            'utilization_component': round(avg_util, 1)
        }

    @staticmethod
    def get_engagement_index():
        """Calculate Classroom Engagement Index (0-100%).

        Based on:
        - Attendance consistency (50%)
        - On-time arrival / punctuality (30%)
        - Active participation proxy = regularity (20%)
        """
        today = date.today()
        month_start = today.replace(day=1)

        # Attendance consistency
        students = Student.query.filter_by(is_active=True).all()
        if not students:
            return {'score': 0, 'status': 'No Data'}

        attendance_pcts = [s.attendance_percentage for s in students]
        avg_attendance = sum(attendance_pcts) / len(attendance_pcts) if attendance_pcts else 0

        # Punctuality: ratio of 'present' to 'late'
        present_count = Attendance.query.filter(
            Attendance.date >= month_start,
            Attendance.status == 'present'
        ).count()
        late_count = Attendance.query.filter(
            Attendance.date >= month_start,
            Attendance.status == 'late'
        ).count()
        total_attending = present_count + late_count
        punctuality = (present_count / total_attending * 100) if total_attending > 0 else 80

        # Regularity: % of students with >80% attendance
        regular_count = sum(1 for p in attendance_pcts if p >= 80)
        regularity = (regular_count / len(students) * 100) if students else 0

        engagement = (
            avg_attendance * 0.50 +
            punctuality * 0.30 +
            regularity * 0.20
        )

        engagement = round(min(100, max(0, engagement)), 1)

        return {
            'score': engagement,
            'attendance_consistency': round(avg_attendance, 1),
            'punctuality': round(punctuality, 1),
            'regularity': round(regularity, 1),
            'status': 'Excellent' if engagement >= 85 else 'Good' if engagement >= 70 else 'Needs Improvement'
        }
