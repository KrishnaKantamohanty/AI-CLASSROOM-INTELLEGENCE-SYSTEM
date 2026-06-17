"""Analytics routes — deep analytics and predictions."""
from flask import Blueprint, render_template
from flask_login import login_required
from app.services.attendance_service import AttendanceService
from app.services.prediction_service import PredictionService
from app.services.health_score import HealthScoreService

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')


@analytics_bp.route('/')
@login_required
def index():
    """Analytics page with heatmaps, predictions, leaderboards."""
    health = HealthScoreService.get_classroom_health_score()
    engagement = HealthScoreService.get_engagement_index()
    at_risk = AttendanceService.get_at_risk_students()
    top_students = AttendanceService.get_top_students(10)
    predictions = PredictionService.predict_attendance_trend(30)

    return render_template('analytics/index.html',
                           health=health,
                           engagement=engagement,
                           at_risk=at_risk,
                           top_students=top_students,
                           predictions=predictions)
