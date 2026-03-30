import logging
import sys
import os
from logging.handlers import RotatingFileHandler

from flask import has_request_context, request

def setup_logger(app):
    # Skip logging setup during testing
    if app.config.get('TESTING'):
        app.logger.setLevel(logging.DEBUG)
        return app.logger
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    class RequestFormatter(logging.Formatter):
        def format(self, record):
            if has_request_context():
                record.url = request.url
                record.remote_addr = request.remote_addr
            else:
                record.url = None
                record.remote_addr = None
            return super().format(record)

    # Create formatters
    console_formatter = RequestFormatter(
        '[%(asctime)s] %(levelname)s - %(remote_addr)s requested %(url)s\n'
        '%(module)s: %(message)s'
    )
    
    file_formatter = RequestFormatter(
        '%(asctime)s - %(levelname)s - [%(remote_addr)s] - %(url)s\n'
        '%(module)s: %(message)s\n'
        'Exception: %(exc_info)s'
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)

    # File Handler with rotation
    file_handler = RotatingFileHandler(
        'logs/app.log', 
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(file_formatter)

    # Set log levels based on environment
    if app.debug:
        console_handler.setLevel(logging.DEBUG)
        file_handler.setLevel(logging.DEBUG)
        app.logger.setLevel(logging.DEBUG)
    else:
        console_handler.setLevel(logging.INFO)
        file_handler.setLevel(logging.INFO)
        app.logger.setLevel(logging.INFO)

    # Remove default handlers and add our custom ones
    app.logger.handlers.clear()
    app.logger.addHandler(console_handler)
    app.logger.addHandler(file_handler)

    # Prevent propagation to root logger
    app.logger.propagate = False

    return app.logger