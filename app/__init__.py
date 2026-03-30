from dotenv import load_dotenv
import time
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
# local
from .extensions import socketio, mail, limiter
from .utils.logging import setup_logger
from .config.config import config_by_name

# Load environment variables
load_dotenv()

# Initialize database
db = SQLAlchemy()

def create_app(config_name='default'):
    app = Flask(__name__)
    
    app.config.from_object(config_by_name[config_name])

    # Configure Redis for production
    if not app.debug:
        # Production: use Redis
        redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
        limiter.init_app(app, storage_uri=f"{redis_url}/limiter")
        socketio.init_app(app, message_queue=f"{redis_url}/socketio")
    else:
        # Development: in-memory
        limiter.init_app(app)
        socketio.init_app(app)

    db.init_app(app)
    mail.init_app(app)

    setup_logger(app)
    
    # Initialize login manager
    login_manager = LoginManager()
    login_manager.login_view = 'frontend.login'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from .views.frontend import frontend_bp
    from .api.jobs import jobs_bp
    from .api.direct_messages import direct_messages_bp
    from .api.notifications import notifications_bp
    from .api.applications import applications_bp
    from .api.profiles import profiles_bp
    
    app.register_blueprint(frontend_bp)
    app.register_blueprint(jobs_bp, url_prefix="/jobs/")
    app.register_blueprint(direct_messages_bp, url_prefix="/messages/")
    app.register_blueprint(notifications_bp, url_prefix="/notifications/")
    app.register_blueprint(applications_bp, url_prefix="/applications/")
    app.register_blueprint(profiles_bp, url_prefix="/profile/")
    
    # Initialize database with connection retry
    with app.app_context():
        from .models import User, Person, Company, Job, JobApplication, Room, Message
        
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                app.logger.info(f"Database initialization: Attempt {retry_count + 1}/{max_retries}")
                app.logger.info("Database initialization: Starting table creation")
                db.create_all()
                app.logger.info("Database initialization: Tables created successfully")
                break
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    app.logger.error(f"Database initialization failed after {max_retries} attempts: {str(e)}")
                    raise
                wait_time = 2 ** retry_count  # Exponential backoff: 2, 4, 8, 16, 32 seconds
                app.logger.warning(f"Database connection failed: {str(e)}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
    
    return app