from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from datetime import datetime

app = Flask(__name__)
CORS(app)


# In-memory storage for users
users = {}
sessions = {}

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "user_service"}), 200

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password') or not data.get('email'):
        return jsonify({"error": "Username, password, and email are required"}), 400
    
    username = data['username']
    password = data['password']
    email = data['email']
    
    # Check if user already exists
    for user_id, user in users.items():
        if user['username'] == username or user['email'] == email:
            return jsonify({"error": "User already exists"}), 409
    
    # Create new user
    user_id = str(uuid.uuid4())
    users[user_id] = {
        'id': user_id,
        'username': username,
        'email': email,
        'password_hash': generate_password_hash(password),
        'full_name': data.get('full_name', ''),
        'bio': data.get('bio', ''),
        'created_at': datetime.now().isoformat(),
        'profile_picture': data.get('profile_picture', '')
    }
    
    return jsonify({
        "message": "User registered successfully",
        "user_id": user_id,
        "username": username
    }), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "Username and password are required"}), 400
    
    username = data['username']
    password = data['password']
    
    # Find user by username
    user = None
    for user_id, u in users.items():
        if u['username'] == username:
            user = u
            break
    
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Create session
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        'user_id': user['id'],
        'username': user['username'],
        'created_at': datetime.now().isoformat()
    }
    
    return jsonify({
        "message": "Login successful",
        "session_id": session_id,
        "user_id": user['id'],
        "username": user['username']
    }), 200

@app.route('/logout', methods=['POST'])
def logout():
    session_id = request.headers.get('Session-ID')
    
    if session_id and session_id in sessions:
        del sessions[session_id]
        return jsonify({"message": "Logout successful"}), 200
    
    return jsonify({"error": "Invalid session"}), 401

@app.route('/profile/<user_id>', methods=['GET'])
def get_profile(user_id):
    if user_id not in users:
        return jsonify({"error": "User not found"}), 404
    
    user = users[user_id].copy()
    # Remove sensitive information
    user.pop('password_hash', None)
    
    return jsonify(user), 200

@app.route('/profile', methods=['PUT'])
def update_profile():
    session_id = request.headers.get('Session-ID')
    
    if not session_id or session_id not in sessions:
        return jsonify({"error": "Authentication required"}), 401
    
    user_id = sessions[session_id]['user_id']
    data = request.get_json()
    
    if user_id not in users:
        return jsonify({"error": "User not found"}), 404
    
    # Update allowed fields including username
    if 'username' in data:
        # Check if username is already taken by another user
        for uid, user in users.items():
            if uid != user_id and user['username'] == data['username']:
                return jsonify({"error": "Username already taken"}), 400
        users[user_id]['username'] = data['username']
        # Update session username as well
        if session_id in sessions:
            sessions[session_id]['username'] = data['username']
    
    allowed_fields = ['full_name', 'bio']
    for field in allowed_fields:
        if field in data:
            users[user_id][field] = data[field]
    
    # Handle profile picture separately if provided
    if 'profile_picture' in data:
        users[user_id]['profile_picture'] = data['profile_picture']
    
    updated_user = users[user_id].copy()
    updated_user.pop('password_hash', None)
    
    return jsonify({
        "message": "Profile updated successfully",
        "user": updated_user
    }), 200


@app.route('/edit_profile', methods=['GET'])
def get_edit_profile():
    session_id = request.headers.get('Session-ID')
    
    if not session_id or session_id not in sessions:
        return jsonify({"error": "Authentication required"}), 401
    
    user_id = sessions[session_id]['user_id']
    
    if user_id not in users:
        return jsonify({"error": "User not found"}), 404
    
    user = users[user_id].copy()
    user.pop('password_hash', None)
    
    return jsonify(user), 200

@app.route('/validate_session', methods=['POST'])
def validate_session():
    session_id = request.headers.get('Session-ID')
    
    if not session_id or session_id not in sessions:
        return jsonify({"valid": False}), 200
    
    session = sessions[session_id]
    return jsonify({
        "valid": True,
        "user_id": session['user_id'],
        "username": session['username']
    }), 200

@app.route('/users/search', methods=['GET'])
def search_users():
    query = request.args.get('q', '').lower()
    
    if not query:
        return jsonify({"users": []}), 200
    
    matching_users = []
    for user_id, user in users.items():
        if (query in user['username'].lower() or 
            query in user.get('full_name', '').lower()):
            user_copy = user.copy()
            user_copy.pop('password_hash', None)
            matching_users.append(user_copy)
    
    return jsonify({"users": matching_users}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)