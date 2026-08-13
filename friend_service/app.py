from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
from datetime import datetime
import requests

app = Flask(__name__)
CORS(app)

# In-memory storage for follows
follows = {}  # user_id -> [following_user_ids]
followers = {}  # user_id -> [follower_user_ids]

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
    return jsonify({"status": "healthy", "service": "follow_service"}), 200

@app.route('/follow', methods=['POST'])
def follow_user():
    session_id = request.headers.get('Session-ID')
    
    # Validate session
    session_data = validate_session(session_id)
    if not session_data.get('valid'):
        return jsonify({"error": "Authentication required"}), 401
    
    data = request.get_json()
    
    if not data or not data.get('user_id'):
        return jsonify({"error": "Target user ID is required"}), 400
    
    follower_id = session_data['user_id']
    following_id = data['user_id']
    
    # Can't follow yourself
    if follower_id == following_id:
        return jsonify({"error": "Cannot follow yourself"}), 400
    
    # Check if already following
    if follower_id in follows and following_id in follows[follower_id]:
        return jsonify({"error": "Already following this user"}), 400
    
    # Add follow relationship
    if follower_id not in follows:
        follows[follower_id] = []
    if following_id not in followers:
        followers[following_id] = []
    
    follows[follower_id].append(following_id)
    followers[following_id].append(follower_id)
    
    # Create notification for the followed user
    try:
        notification_data = {
            'user_id': following_id,
            'type': 'follow',
            'message': f'{session_data["username"]} started following you',
            'from_user_id': follower_id,
            'from_username': session_data['username']
        }
        requests.post('http://localhost:5005/notifications', json=notification_data)
    except:
        pass  # Don't fail if notification service is down
    
    return jsonify({
        "message": "Successfully followed user",
        "following_id": following_id
    }), 201

@app.route('/unfollow', methods=['POST'])
def unfollow_user():
    session_id = request.headers.get('Session-ID')
    
    # Validate session
    session_data = validate_session(session_id)
    if not session_data.get('valid'):
        return jsonify({"error": "Authentication required"}), 401
    
    data = request.get_json()
    
    if not data or not data.get('user_id'):
        return jsonify({"error": "Target user ID is required"}), 400
    
    follower_id = session_data['user_id']
    following_id = data['user_id']
    
    # Check if currently following
    if (follower_id not in follows or following_id not in follows[follower_id]):
        return jsonify({"error": "Not following this user"}), 400
    
    # Remove follow relationship
    follows[follower_id].remove(following_id)
    if following_id in followers:
        followers[following_id].remove(follower_id)
    
    return jsonify({
        "message": "Successfully unfollowed user",
        "unfollowed_id": following_id
    }), 200

@app.route('/following/<user_id>', methods=['GET'])
def get_following(user_id):
    """Get list of users that this user is following"""
    following_ids = follows.get(user_id, [])
    
    # Get user details for each following
    following_list = []
    for following_id in following_ids:
        try:
            response = requests.get(f"{USER_SERVICE_URL}/profile/{following_id}")
            if response.status_code == 200:
                user_data = response.json()
                following_list.append({
                    'user_id': following_id,
                    'username': user_data.get('username'),
                    'full_name': user_data.get('full_name'),
                    'profile_picture': user_data.get('profile_picture')
                })
        except:
            continue
    
    return jsonify({
        "following": following_list,
        "following_count": len(following_ids)
    }), 200

@app.route('/followers/<user_id>', methods=['GET'])
def get_followers(user_id):
    """Get list of users that follow this user"""
    follower_ids = followers.get(user_id, [])
    
    # Get user details for each follower
    follower_list = []
    for follower_id in follower_ids:
        try:
            response = requests.get(f"{USER_SERVICE_URL}/profile/{follower_id}")
            if response.status_code == 200:
                user_data = response.json()
                follower_list.append({
                    'user_id': follower_id,
                    'username': user_data.get('username'),
                    'full_name': user_data.get('full_name'),
                    'profile_picture': user_data.get('profile_picture')
                })
        except:
            continue
    
    return jsonify({
        "followers": follower_list,
        "followers_count": len(follower_ids)
    }), 200

@app.route('/follow_status/<other_user_id>', methods=['GET'])
def get_follow_status(other_user_id):
    session_id = request.headers.get('Session-ID')
    
    # Validate session
    session_data = validate_session(session_id)
    if not session_data.get('valid'):
        return jsonify({"error": "Authentication required"}), 401
    
    user_id = session_data['user_id']
    
    # Check if user is following the other user
    is_following = user_id in follows and other_user_id in follows[user_id]
    
    # Check if the other user is following this user
    follows_back = other_user_id in follows and user_id in follows[other_user_id]
    
    return jsonify({
        "is_following": is_following,
        "follows_back": follows_back
    }), 200

@app.route('/stats/<user_id>', methods=['GET'])
def get_follow_stats(user_id):
    """Get follower/following counts for a user"""
    following_count = len(follows.get(user_id, []))
    followers_count = len(followers.get(user_id, []))
    
    return jsonify({
        "following_count": following_count,
        "followers_count": followers_count
    }), 200

# Legacy endpoints for API compatibility during transition
@app.route('/friends/<user_id>', methods=['GET'])
def get_friends_legacy(user_id):
    """Legacy endpoint - now returns following list"""
    return get_following(user_id)

@app.route('/friendship_status/<other_user_id>', methods=['GET'])
def get_friendship_status_legacy(other_user_id):
    """Legacy endpoint - now returns follow status"""
    return get_follow_status(other_user_id)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)