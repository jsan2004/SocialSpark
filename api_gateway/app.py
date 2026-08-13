from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
import requests
from werkzeug.datastructures import FileStorage

app = Flask(__name__)
CORS(app)

# Service URLs
SERVICES = {
    'user': 'http://localhost:5001',
    'post': 'http://localhost:5002',
    'follow': 'http://localhost:5003',
    'notification': 'http://localhost:5005',
    'frontend': 'http://localhost:5000'
}

def forward_request(service_url, path, method='GET', headers=None, json_data=None, params=None, files=None):
    """Forward request to appropriate microservice"""
    try:
        url = f"{service_url}{path}"
        
        # Prepare headers
        forward_headers = {}
        if headers:
            # Forward specific headers
            if 'Session-ID' in headers:
                forward_headers['Session-ID'] = headers['Session-ID']
            # Don't forward Content-Type for multipart uploads
            if 'Content-Type' in headers and not files:
                forward_headers['Content-Type'] = headers['Content-Type']
        
        # Make request to microservice
        if method == 'GET':
            response = requests.get(url, headers=forward_headers, params=params)
        elif method == 'POST':
            if files:
                response = requests.post(url, headers=forward_headers, files=files)
            else:
                response = requests.post(url, headers=forward_headers, json=json_data)
        elif method == 'PUT':
            response = requests.put(url, headers=forward_headers, json=json_data)
        elif method == 'DELETE':
            response = requests.delete(url, headers=forward_headers)
        else:
            return jsonify({"error": "Method not supported"}), 405
        
        # Return response from microservice
        try:
            return response.json(), response.status_code
        except:
            return {"message": "Response received"}, response.status_code
            
    except requests.exceptions.ConnectionError:
        return jsonify({"error": f"Service unavailable"}), 503
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "api_gateway"}), 200

# User Service Routes
@app.route('/api/register', methods=['POST'])
def register():
    return forward_request(SERVICES['user'], '/register', 'POST', 
                         headers=request.headers, json_data=request.get_json())

@app.route('/api/login', methods=['POST'])
def login():
    return forward_request(SERVICES['user'], '/login', 'POST', 
                         headers=request.headers, json_data=request.get_json())

@app.route('/api/logout', methods=['POST'])
def logout():
    return forward_request(SERVICES['user'], '/logout', 'POST', 
                         headers=request.headers)

@app.route('/api/profile/<user_id>', methods=['GET'])
def get_profile(user_id):
    return forward_request(SERVICES['user'], f'/profile/{user_id}', 'GET', 
                         headers=request.headers)

@app.route('/api/profile', methods=['PUT'])
def update_profile():
    return forward_request(SERVICES['user'], '/profile', 'PUT', 
                         headers=request.headers, json_data=request.get_json())

@app.route('/api/users/search', methods=['GET'])
def search_users():
    return forward_request(SERVICES['user'], '/users/search', 'GET', 
                         headers=request.headers, params=request.args)



# Post Service Routes
@app.route('/api/posts', methods=['GET', 'POST'])
def posts():
    if request.method == 'GET':
        return forward_request(SERVICES['post'], '/posts', 'GET', 
                             headers=request.headers, params=request.args)
    else:
        return forward_request(SERVICES['post'], '/posts', 'POST', 
                             headers=request.headers, json_data=request.get_json())

@app.route('/api/posts/<post_id>/comments', methods=['GET', 'POST'])
def post_comments(post_id):
    if request.method == 'GET':
        return forward_request(SERVICES['post'], f'/posts/{post_id}/comments', 'GET', 
                             headers=request.headers)
    else:
        return forward_request(SERVICES['post'], f'/posts/{post_id}/comments', 'POST', 
                             headers=request.headers, json_data=request.get_json())

@app.route('/api/posts/<post_id>/comments/<comment_id>', methods=['DELETE'])
def delete_comment(post_id, comment_id):
    return forward_request(SERVICES['post'], f'/posts/{post_id}/comments/{comment_id}', 'DELETE', 
                         headers=request.headers)

@app.route('/api/posts/<post_id>', methods=['GET', 'DELETE'])
def post_detail(post_id):
    return forward_request(SERVICES['post'], f'/posts/{post_id}', request.method, 
                         headers=request.headers)

@app.route('/api/posts/<post_id>/like', methods=['POST'])
def like_post(post_id):
    return forward_request(SERVICES['post'], f'/posts/{post_id}/like', 'POST', 
                         headers=request.headers)

@app.route('/api/posts/feed', methods=['GET'])
def get_feed():
    return forward_request(SERVICES['post'], '/posts/feed', 'GET', 
                         headers=request.headers, params=request.args)

# Follow Service Routes
@app.route('/api/follow', methods=['POST'])
def follow_user():
    return forward_request(SERVICES['follow'], '/follow', 'POST', 
                         headers=request.headers, json_data=request.get_json())

@app.route('/api/unfollow', methods=['POST'])
def unfollow_user():
    return forward_request(SERVICES['follow'], '/unfollow', 'POST', 
                         headers=request.headers, json_data=request.get_json())

@app.route('/api/following/<user_id>', methods=['GET'])
def get_following(user_id):
    return forward_request(SERVICES['follow'], f'/following/{user_id}', 'GET', 
                         headers=request.headers)

@app.route('/api/followers/<user_id>', methods=['GET'])
def get_followers(user_id):
    return forward_request(SERVICES['follow'], f'/followers/{user_id}', 'GET', 
                         headers=request.headers)

@app.route('/api/follow_status/<other_user_id>', methods=['GET'])
def get_follow_status(other_user_id):
    return forward_request(SERVICES['follow'], f'/follow_status/{other_user_id}', 'GET', 
                         headers=request.headers)

@app.route('/api/stats/<user_id>', methods=['GET'])
def get_follow_stats(user_id):
    return forward_request(SERVICES['follow'], f'/stats/{user_id}', 'GET', 
                         headers=request.headers)

# Legacy routes for backward compatibility
@app.route('/api/friends/<user_id>', methods=['GET'])
def get_friends_legacy(user_id):
    return forward_request(SERVICES['follow'], f'/friends/{user_id}', 'GET', 
                         headers=request.headers)

@app.route('/api/friendship_status/<other_user_id>', methods=['GET'])
def get_friendship_status_legacy(other_user_id):
    return forward_request(SERVICES['follow'], f'/friendship_status/{other_user_id}', 'GET', 
                         headers=request.headers)

# Notification Service Routes
@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    return forward_request(SERVICES['notification'], '/notifications', 'GET', 
                         headers=request.headers, params=request.args)

@app.route('/api/notifications/<notification_id>/read', methods=['POST'])
def mark_notification_read(notification_id):
    return forward_request(SERVICES['notification'], f'/notifications/{notification_id}/read', 'POST', 
                         headers=request.headers)

@app.route('/api/notifications/mark_all_read', methods=['POST'])
def mark_all_notifications_read():
    return forward_request(SERVICES['notification'], '/notifications/mark_all_read', 'POST', 
                         headers=request.headers)

@app.route('/api/notifications/unread_count', methods=['GET'])
def get_unread_count():
    return forward_request(SERVICES['notification'], '/notifications/unread_count', 'GET', 
                         headers=request.headers)

# Additional notification service routes
@app.route('/api/notifications', methods=['POST'])
def create_notification():
    return forward_request(SERVICES['notification'], '/notifications', 'POST', 
                         headers=request.headers, json_data=request.get_json())

# Missing follow service routes
@app.route('/api/follow_status/<other_user_id>', methods=['GET'])
def get_follow_status_new(other_user_id):
    return forward_request(SERVICES['follow'], f'/follow_status/{other_user_id}', 'GET', 
                         headers=request.headers)

# Comments routes
@app.route('/api/posts/<post_id>/comments', methods=['GET'])
def get_post_comments(post_id):
    return forward_request(SERVICES['post'], f'/posts/{post_id}/comments', 'GET', 
                         headers=request.headers)

@app.route('/api/posts/<post_id>/comments', methods=['POST'])
def add_post_comment(post_id):
    return forward_request(SERVICES['post'], f'/posts/{post_id}/comments', 'POST', 
                         headers=request.headers, json_data=request.get_json())

# Profile editing routes - fixed endpoints
@app.route('/api/profile/edit', methods=['GET'])
def get_edit_profile_new():
    # Extract user ID from session and get their profile
    session_id = request.headers.get('Session-ID')
    if not session_id:
        return jsonify({"error": "Authentication required"}), 401
    
    # First validate session to get user_id
    session_response = requests.post('http://localhost:5001/validate_session', 
                                   headers={'Session-ID': session_id})
    if session_response.status_code != 200:
        return jsonify({"error": "Authentication required"}), 401
    
    session_data = session_response.json()
    if not session_data.get('valid'):
        return jsonify({"error": "Authentication required"}), 401
    
    user_id = session_data.get('user_id')
    return forward_request(SERVICES['user'], f'/profile/{user_id}', 'GET', 
                         headers=request.headers)

@app.route('/api/profile/edit', methods=['PUT'])
def update_profile_edit():
    return forward_request(SERVICES['user'], '/profile', 'PUT', 
                         headers=request.headers, json_data=request.get_json())

# Root route - redirect to frontend
@app.route('/')
def index():
    return redirect(SERVICES['frontend'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=True)