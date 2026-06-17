"""Dashboard routes — main dashboard page."""
from flask import Blueprint, render_template
from flask_login import login_required
from app.services.attendance_service import AttendanceService
from app.services.health_score import HealthScoreService
from app.services.insight_engine import InsightEngine
from app.services.detection_service import get_detection_service

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard with stats, charts, insights, and AI analytics."""
    # Generate fresh insights
    try:
        InsightEngine.generate_all_insights()
    except Exception:
        pass

    # Gather all dashboard data
    stats = AttendanceService.get_today_stats()
    health = HealthScoreService.get_classroom_health_score()
    engagement = HealthScoreService.get_engagement_index()
    at_risk = AttendanceService.get_at_risk_students()
    top_students = AttendanceService.get_top_students(5)
    insights = InsightEngine.get_active_insights(8)
    new_this_month = AttendanceService.get_new_students_this_month()

    # Detection stats
    detection_svc = get_detection_service()
    detection_stats = detection_svc.get_live_stats()

    # Attendance rates
    rates = {
        'daily': AttendanceService.get_attendance_rate('daily'),
        'weekly': AttendanceService.get_attendance_rate('weekly'),
        'monthly': AttendanceService.get_attendance_rate('monthly'),
        'semester': AttendanceService.get_attendance_rate('semester'),
    }

    # Occupancy info
    from app.models.classroom import Classroom
    classroom = Classroom.query.first()
    occupancy = {
        'capacity': classroom.capacity if classroom else 60,
        'present': detection_stats['current_count'],
        'percentage': round(detection_stats['current_count'] / (classroom.capacity if classroom else 60) * 100, 1)
    }

    return render_template('dashboard/index.html',
                           stats=stats,
                           health=health,
                           engagement=engagement,
                           at_risk=at_risk,
                           top_students=top_students,
                           insights=insights,
                           new_this_month=new_this_month,
                           detection_stats=detection_stats,
                           rates=rates,
                           occupancy=occupancy)
