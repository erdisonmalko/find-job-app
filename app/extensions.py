from flask_socketio import SocketIO
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# DO NOT bind to app here
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode='eventlet',  # Use eventlet for async
    message_queue=None  # Will be set in app factory based on env
)
mail = Mail()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=None  # Will be configured in app factory
)