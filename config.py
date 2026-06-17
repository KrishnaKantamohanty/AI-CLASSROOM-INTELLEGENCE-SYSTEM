import os
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'ai-classroom-secret-key-change-in-production')
    db_path = os.path.join(basedir, 'classroom.db').replace('\\', '/')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f'sqlite:///{db_path}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # AI / Detection
    YOLO_MODEL_PATH = os.path.join(basedir, 'ai_models', 'yolov8n.pt')
    DETECTION_CONFIDENCE = 0.5
    USE_SIMULATION = True  # Set False to use real camera + YOLO

    # Camera
    CAMERA_SOURCE = 0  # 0 = webcam, or RTSP URL string
    CAMERA_FPS = 15

    # Classroom defaults
    DEFAULT_CLASSROOM_CAPACITY = 60

    # Report output
    REPORT_DIR = os.path.join(basedir, 'data', 'reports')

    # Attendance thresholds
    ATTENDANCE_RISK_THRESHOLD = 75  # percentage
    ATTENDANCE_CRITICAL_THRESHOLD = 50

    # Image Uploads
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads', 'students')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB limit
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


class DevelopmentConfig(Config):
    DEBUG = True
    USE_SIMULATION = True


class ProductionConfig(Config):
    DEBUG = False
    USE_SIMULATION = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    USE_SIMULATION = True


config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
