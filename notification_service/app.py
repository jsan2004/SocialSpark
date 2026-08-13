from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
from datetime import datetime
import requests

app = Flask(__name__)
CORS(app)

# In-memory storage for notifications
notifications = {}  # user_id -> [notification_objects]

# User service URL
USER_SERVICE_URL = "http://localhost:5001"

def validate_session(session_id):
    """Validate session with user service"""
    try:
        response = requests.post(
            f"{USER_SERVICE_URL}/validate_session",
            headers={"Session-ID": session_id}
        )
        if response.status_code == 200:
            return response.json()
        return {"valid": False}
    except:
        return {"valid": False}

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "notification_service"}), 200

@app.route('/notifications', methods=['GET'])
def get_notifications():
    session_id = request.headers.get('Session-ID')
    
    # Validate session
    session_data = validate_session(session_id)
    if not session_data.get('valid'):
        return jsonify({"error": "Authentication required"}), 401
    
    user_id = session_data['user_id']
    limit = int(request.args.get('limit', 50))
    
    user_notifications = notifications.get(user_id, [])
    
    # Sort by creation time (newest first)
    user_notifications.sort(key=lambda x: x['created_at'], reverse=True)
    
    # Apply limit
    user_notifications = user_notifications[:limit]
    
    return jsonify({"notifications": user_notifications}), 200

@app.route('/notifications', methods=['POST'])
def create_notification():
    """Create a notification for a user (internal service call)"""
    data = request.get_json()
    
    if not data or not data.get('user_id') or not data.get('type') or not data.get('message'):
        return jsonify({"error": "user_id, type, and message are required"}), 400
    
    user_id = data['user_id']
    notification_id = str(uuid.uuid4())
    
    notification = {
        'id': notification_id,
        'type': data['type'],  # 'follow', 'like', 'comment'
        'message': data['message'],
        'from_user_id': data.get('from_user_id'),
        'from_username': data.get('from_username'),
        'post_id': data.get('post_id'),
        'created_at': datetime.now().isoformat(),
        'read': False
    }
    
    if user_id not in notifications:
        notifications[user_id] = []
    
    notifications[user_id].append(notification)
    
    return jsonify({
        "message": "Notification created successfully",
        "notification": notification
    }), 201

@app.route('/notifications/<notification_id>/read', methods=['POST'])
def mark_notification_read(notification_id):
    session_id = request.headers.get('Session-ID')
    
    # Validate session
    session_data = validate_session(session_id)
    if not session_data.get('valid'):
        return jsonify({"error": "Authentication required"}), 401
    
    user_id = session_data['user_id']
    
    # Find and mark notification as read
    for notification in notifications.get(user_id, []):
        if notification['id'] == notification_id:
            notification['read'] = True
            return jsonify({"message": "Notification marked as read"}), 200
    
    return jsonify({"error": "Notification not found"}), 404

@app.route('/notifications/mark_all_read', methods=['POST'])
def mark_all_notifications_read():
    session_id = request.headers.get('Session-ID')
    
    # Validate session
    session_data = validate_session(session_id)
    if not session_data.get('valid'):
        return jsonify({"error": "Authentication required"}), 401
    
    user_id = session_data['user_id']
    
    # Mark all notifications as read
    for notification in notifications.get(user_id, []):
        notification['read'] = True
    
    return jsonify({"message": "All notifications marked as read"}), 200

@app.route('/notifications/unread_count', methods=['GET'])
def get_unread_count():
    session_id = request.headers.get('Session-ID')
    
    # Validate session
    session_data = validate_session(session_id)
    if not session_data.get('valid'):
        return jsonify({"error": "Authentication required"}), 401
    
    user_id = session_data['user_id']
    
    unread_count = 0
    for notification in notifications.get(user_id, []):
        if not notification['read']:
            unread_count += 1
    
    return jsonify({"unread_count": unread_count}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)