"""AI Classroom Intelligence System — Flask App Factory."""
import os
from flask import Flask
from config import config_map


def create_app(config_name=None):
    """Create and configure the Flask application."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_map.get(config_name, config_map['default']))

    # Ensure instance, report, and upload directories exist
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config.get('REPORT_DIR', 'data/reports'), exist_ok=True)
    if app.config.get('UPLOAD_FOLDER'):
        os.makedirs(app.config.get('UPLOAD_FOLDER'), exist_ok=True)
        # Create temp dir for image-based attendance processing
        os.makedirs(os.path.join(app.config.get('UPLOAD_FOLDER'), 'temp'), exist_ok=True)

    # Initialize extensions
    from app.extensions import db, login_manager, csrf
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # User loader for Flask-Login
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.students import students_bp
    from app.routes.attendance import attendance_bp
    from app.routes.camera import camera_bp
    from app.routes.reports import reports_bp
    from app.routes.analytics import analytics_bp
    from app.routes.api import api_bp
    from app.routes.checkin import checkin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(camera_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(checkin_bp)

    # Exempt public check-in routes from CSRF
    csrf.exempt(checkin_bp)

    # Create database tables
    with app.app_context():
        from app.models import user, student, teacher, attendance, classroom, ai_insight, report, attendance_session  # noqa: F811,F401
        db.create_all()

    # Register error handlers
    @app.errorhandler(404)
    def not_found(e):
        return '<h1>404 — Page Not Found</h1>', 404

    @app.errorhandler(500)
    def server_error(e):
        return '<h1>500 — Internal Server Error</h1>', 500

    # Jinja2 context processor — inject current year
    @app.context_processor
    def inject_globals():
        from datetime import datetime
        return {'current_year': datetime.now().year}

    return app
