"""Attendance Service — analytics, risk detection, and statistics."""
from datetime import datetime, timedelta, date
from sqlalchemy import func, and_
from app.extensions import db
from app.models.attendance import Attendance
from app.models.student import Student


class AttendanceService:
    """Business logic for attendance analytics."""

    @staticmethod
    def get_today_stats():
        """Get today's attendance statistics."""
        today = date.today()
        total_students = Student.query.filter_by(is_active=True).count()
        present_today = Attendance.query.filter(
            Attendance.date == today,
            Attendance.status.in_(['present', 'late'])
        ).count()
        absent_today = total_students - present_today

        return {
            'total_students': total_students,
            'present_today': present_today,
            'absent_today': absent_today,
            'attendance_rate': round((present_today / total_students * 100), 1) if total_students > 0 else 0
        }

    @staticmethod
    def get_attendance_rate(period='daily'):
        """Calculate attendance rate for a given period."""
        today = date.today()

        if period == 'daily':
            start_date = today
        elif period == 'weekly':
            start_date = today - timedelta(days=today.weekday())
        elif period == 'monthly':
            start_date = today.replace(day=1)
        elif period == 'semester':
            start_date = today - timedelta(days=180)
        else:
            start_date = today

        total = Attendance.query.filter(Attendance.date >= start_date).count()
        present = Attendance.query.filter(
            Attendance.date >= start_date,
            Attendance.status.in_(['present', 'late'])
        ).count()

        return round((present / total * 100), 1) if total > 0 else 0

    @staticmethod
    def get_attendance_trend(days=30):
        """Get daily attendance counts for the last N days."""
        today = date.today()
        start = today - timedelta(days=days)

        results = db.session.query(
            Attendance.date,
            func.count(Attendance.id).label('total'),
            func.sum(
                db.case(
                    (Attendance.status.in_(['present', 'late']), 1),
                    else_=0
                )
            ).label('present')
        ).filter(
            Attendance.date >= start
        ).group_by(Attendance.date).order_by(Attendance.date).all()

        labels = []
        present_data = []
        absent_data = []
        rates = []

        for row in results:
            labels.append(row.date.strftime('%b %d'))
            p = int(row.present or 0)
            t = int(row.total or 0)
            present_data.append(p)
            absent_data.append(t - p)
            rates.append(round(p / t * 100, 1) if t > 0 else 0)

        return {
            'labels': labels,
            'present': present_data,
            'absent': absent_data,
            'rates': rates
        }

    @staticmethod
    def get_day_wise_attendance():
        """Get average attendance by day of week."""
        results = db.session.query(
            func.strftime('%w', Attendance.date).label('dow'),
            func.count(Attendance.id).label('total'),
            func.sum(
                db.case(
                    (Attendance.status.in_(['present', 'late']), 1),
                    else_=0
                )
            ).label('present')
        ).group_by('dow').all()

        day_names = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        data = {str(i): 0 for i in range(7)}

        for row in results:
            dow = str(row.dow)
            total = int(row.total or 0)
            present = int(row.present or 0)
            data[dow] = round(present / total * 100, 1) if total > 0 else 0

        return {
            'labels': day_names,
            'data': [data.get(str(i), 0) for i in range(7)]
        }

    @staticmethod
    def get_at_risk_students():
        """Find students with attendance below threshold."""
        students = Student.query.filter_by(is_active=True).all()
        at_risk = []

        for s in students:
            pct = s.attendance_percentage
            if pct < 75:
                # Check consecutive absences
                recent = Attendance.query.filter_by(student_id=s.id).order_by(
                    Attendance.date.desc()
                ).limit(10).all()
                consecutive = 0
                for rec in recent:
                    if rec.status == 'absent':
                        consecutive += 1
                    else:
                        break

                risk = 'critical' if pct < 50 else 'at_risk'
                recommendation = 'Immediate intervention required' if risk == 'critical' \
                    else 'Schedule counseling session'

                at_risk.append({
                    'id': s.id,
                    'name': s.name,
                    'roll_number': s.roll_number,
                    'department': s.department,
                    'attendance_pct': pct,
                    'consecutive_absences': consecutive,
                    'risk_level': risk,
                    'recommendation': recommendation
                })

        # Sort by attendance (lowest first)
        at_risk.sort(key=lambda x: x['attendance_pct'])
        return at_risk

    @staticmethod
    def get_monthly_heatmap_data():
        """Generate attendance heatmap data (day × week)."""
        today = date.today()
        start = today - timedelta(days=90)

        results = db.session.query(
            Attendance.date,
            func.count(Attendance.id).label('total'),
            func.sum(
                db.case(
                    (Attendance.status.in_(['present', 'late']), 1),
                    else_=0
                )
            ).label('present')
        ).filter(Attendance.date >= start).group_by(Attendance.date).all()

        heatmap = {}
        for row in results:
            d = row.date
            total = int(row.total or 0)
            present = int(row.present or 0)
            rate = round(present / total * 100, 1) if total > 0 else 0
            week_num = d.isocalendar()[1]
            day_num = d.weekday()
            key = f'{week_num}-{day_num}'
            heatmap[key] = rate

        return heatmap

    @staticmethod
    def get_top_students(limit=10):
        """Get students with highest attendance."""
        students = Student.query.filter_by(is_active=True).all()
        ranked = [(s, s.attendance_percentage) for s in students]
        ranked.sort(key=lambda x: x[1], reverse=True)

        return [{
            'id': s.id,
            'name': s.name,
            'roll_number': s.roll_number,
            'department': s.department,
            'attendance_pct': pct
        } for s, pct in ranked[:limit]]

    @staticmethod
    def get_new_students_this_month():
        """Count students enrolled this month."""
        today = date.today()
        first_of_month = today.replace(day=1)
        return Student.query.filter(
            Student.enrolled_date >= datetime.combine(first_of_month, datetime.min.time())
        ).count()
