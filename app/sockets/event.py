from app.extensions import socketio
from flask import current_app

@socketio.on('connect')
def handle_connect():
    current_app.logger.info("Socket connected")