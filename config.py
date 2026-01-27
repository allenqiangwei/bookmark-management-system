import os
from datetime import timedelta

class Config:
    """应用配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set")
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///instance/bookmarks.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_ATTEMPT_WINDOW = 900  # 15分钟（秒）

    # Session security
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_DEBUG') != 'True'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Remember Me cookie security
    REMEMBER_COOKIE_SECURE = os.environ.get('FLASK_DEBUG') != 'True'
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
