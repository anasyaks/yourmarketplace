import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Security - CRITICAL for sessions
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here-CHANGE-THIS-IN-PRODUCTION')

    # Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///marketplace.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File Uploads
    UPLOAD_FOLDER = 'app/static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB

    # Admin Credentials (override with env vars in production)
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@marketplace.com')
