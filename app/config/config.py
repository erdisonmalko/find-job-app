import os
from dotenv import load_dotenv
# read env file from root folder

load_dotenv()

class Config:
    """Base config class"""
    # Basic Flask config
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-prod')
    
    # File upload config
    MEGABYTE = (2 ** 10) ** 2
    MAX_CONTENT_LENGTH = 50 * MEGABYTE
    MAX_FORM_MEMORY_SIZE = 50 * MEGABYTE
    
    # Database config
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # Test connection before using
        'pool_recycle': 3600,   # Recycle connections every hour
        'pool_size': 10,        # Connection pool size
        'max_overflow': 20,     # Max overflow connections
    }
    
    # Mail config
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
    SECURITY_PASSWORD_SALT = os.getenv("SECURITY_PASSWORD_SALT")
    
    # Redis config (for rate limiter and WebSocket)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

class DevelopmentConfig(Config):
    """Development config"""
    DEBUG = True
    DEVELOPMENT = True
    UPLOAD_FOLDER = 'app/static/resume_upload'
    # Use in-memory for rate limiter in development
    RATELIMIT_STORAGE_URL = None  # Falls back to in-memory

    def is_development(self):
        return True

class ProductionConfig(Config):
    """Production config"""
    DEBUG = False
    DEVELOPMENT = False
    UPLOAD_FOLDER = os.getenv('PROD_UPLOAD_FOLDER', 'app/static/resume_upload')
    # Use Redis for rate limiter in production
    RATELIMIT_STORAGE_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/1')

    def is_production(self):
        return True

class TestingConfig(Config):
    """Testing config"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URI')
    UPLOAD_FOLDER = 'tests/test_uploads'

# Dictionary to map config names to config classes
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}