"""API routes — JSON endpoints for charts and real-time updates."""
from flask import Blueprint, jsonify, current_app
from flask_login import login_required
from app.services.attendance_service import AttendanceService
from app.services.detection_service import get_detection_service
from app.services.health_score import HealthScoreService
from app.services.prediction_service import PredictionService
from app.services.insight_engine import InsightEngine

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/stats')
@login_required
def stats():
    """Get dashboard statistics."""
    data = AttendanceService.get_today_stats()
    data['new_this_month'] = AttendanceService.get_new_students_this_month()
    return jsonify(data)


@api_bp.route('/attendance-trend')
@login_required
def attendance_trend():
    """Get attendance trend data for charts."""
    return jsonify(AttendanceService.get_attendance_trend(30))


@api_bp.route('/day-wise')
@login_required
def day_wise():
    """Get day-wise attendance data."""
    return jsonify(AttendanceService.get_day_wise_attendance())


@api_bp.route('/occupancy')
@login_required
def occupancy():
    """Get real-time occupancy data."""
    svc = get_detection_service(current_app)
    stats = svc.get_live_stats()
    from app.models.classroom import Classroom
    classroom = Classroom.query.first()
    capacity = classroom.capacity if classroom else 60

    return jsonify({
        'current': stats['current_count'],
        'capacity': capacity,
        'percentage': round(stats['current_count'] / capacity * 100, 1),
        'peak': stats['peak_occupancy'],
        'lowest': stats['lowest_occupancy'],
        'confidence': stats['average_confidence'],
        'mode': stats['detection_mode']
    })


@api_bp.route('/health')
@login_required
def health():
    """Get classroom health score."""
    return jsonify(HealthScoreService.get_classroom_health_score())


@api_bp.route('/engagement')
@login_required
def engagement():
    """Get engagement index."""
    return jsonify(HealthScoreService.get_engagement_index())


@api_bp.route('/predictions')
@login_required
def predictions():
    """Get attendance predictions."""
    return jsonify(PredictionService.predict_attendance_trend(30))


@api_bp.route('/insights')
@login_required
def insights():
    """Get AI insights."""
    active = InsightEngine.get_active_insights(10)
    return jsonify([{
        'id': i.id,
        'text': i.insight_text,
        'category': i.category,
        'severity': i.severity,
        'icon': i.icon,
        'time': i.generated_at.strftime('%H:%M')
    } for i in active])


@api_bp.route('/at-risk')
@login_required
def at_risk():
    """Get at-risk students."""
    return jsonify(AttendanceService.get_at_risk_students())


@api_bp.route('/rates')
@login_required
def rates():
    """Get attendance rates for all periods."""
    return jsonify({
        'daily': AttendanceService.get_attendance_rate('daily'),
        'weekly': AttendanceService.get_attendance_rate('weekly'),
        'monthly': AttendanceService.get_attendance_rate('monthly'),
        'semester': AttendanceService.get_attendance_rate('semester'),
    })
