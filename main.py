import os
from app import create_app
from app.extensions import socketio

# Determine config based on environment
config_name = os.getenv('FLASK_ENV', 'development')
app = create_app(config_name)

if __name__ == "__main__":
    # Development mode: use socketio.run()
    if app.debug:
        socketio.run(
            app,
            host="0.0.0.0",
            port=5001,
            debug=True,
            use_reloader=True
        )
    else:
        # Production mode: run with gunicorn (CLI command)
        # This block won't execute in production as gunicorn handles it
        import sys
        sys.stderr.write("Running in production mode. Use gunicorn to start the server.\n")
        sys.stderr.write("Example: gunicorn -k eventlet -w 1 main:app --bind 0.0.0.0:${PORT:-5001}\n")