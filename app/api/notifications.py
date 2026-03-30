from datetime import datetime

from flask import Blueprint, request,jsonify,current_app
from flask_login import login_required, current_user
from flask_socketio import join_room,emit
# local
from app import db
from app.models import  Notifications
from app.extensions import socketio, limiter

notifications_bp = Blueprint("notifications",__name__)

# mark a single notification as read
@notifications_bp.route("/notification/mark_read/<int:notification_id>", methods=["POST"])
@limiter.limit("5 per minute")
@login_required
def mark_notification_read(notification_id):
    notification = Notifications.query.get(notification_id)
    if notification and notification.receiver_id == current_user.id:
        notification.read = True
        db.session.commit()
        # log
        current_app.logger.info(f"Notification id: {notification_id} mark as read")
        return jsonify({"message": "Notification mark as read"}),200
    
    return jsonify({"error": "Notification not found"}), 404

# mark all user's notifications as read
@notifications_bp.route("/notification/mark_all_read", methods=["POST"])
@limiter.limit("1 per minute")
@login_required
def mark_all_read():
    all_current_user_notifications = Notifications.query.filter_by(receiver_id=current_user.id).all()
    for notification in all_current_user_notifications:
        notification.read = True
        db.session.commit()
        # log
        current_app.logger.info(f"Notifications for user: {current_user.name} mark as read")
        return jsonify({"message": "Notifications mark as read"}),200
    
    return jsonify({"error": "No notifications found"}), 404

# delete a notification
@notifications_bp.route("/notification/delete/<int:notification_id>", methods=["POST"])
@limiter.limit("5 per minute")
@login_required
def delete_notification(notification_id):
    notification = Notifications.query.get(notification_id)
    if notification and notification.receiver_id == current_user.id:
        db.session.delete(notification)
        db.session.commit()
        # log
        current_app.logger.info(f"Notification id:{notification_id} for user: {current_user.name} deleted")
        return jsonify({"message": "Notification deleted"}),200
    
    return jsonify({"error": "Notification not found"}), 404



#socket to handle new notifications
@socketio.on("join_notifications")
def handle_join_notifications(data):
    """Handle user joining their notification room"""
    if not current_user.is_authenticated:
        emit('error', {'message': 'User not authenticated'}, room=request.sid)
    try:
        # Get user info from data
        user_id = data.get('user_id')
        user_type = data.get('user_type')
        
        if not user_id:
            current_app.logger.critical("Error: No user_id provided in join_notifications")
            return
        
        # Create a unique room name for user's notifications
        notification_room = f"notifications_{user_id}"
        
        # Join the room
        join_room(notification_room)
        
        current_app.logger.info(f"User {user_id} ({user_type}) joined notification room: {notification_room}")
        
        # Optionally send confirmation
        return {"status": "success", "message": "Joined notification room"}
        
    except Exception as e:
        current_app.logger.error(f"Error in handle_join_notifications: {str(e)}")
        return {"status": "error", "message": str(e)}




def create_notification(receiver_id, message,emit_notification=False):
    """
    Create a new notification record.
    Optionally, if emit_notification is True, emit a real-time update.
    """
    new_notification = Notifications(
        receiver_id=receiver_id,
        message=message,
        read=False,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    try:
        db.session.add(new_notification)
        db.session.commit()
        current_app.logger.info(f"Notification added to DB correctly {new_notification.id}")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating notification: {e}")
        return None

    if emit_notification:
            notification_room = f"notifications_{receiver_id}"
            socketio.emit('new_notification', 
                         new_notification.__json__(), 
                         room=notification_room)
            current_app.logger.info(f"Emitted notification to room: {notification_room}")
            
    return new_notification


