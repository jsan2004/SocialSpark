from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
from datetime import datetime
import requests

app = Flask(__name__)
CORS(app)

# In-memory storage for posts and comments
posts = {}
comments = {}  # comment_id -> {id, post_id, user_id, username, content, created_at}

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
    return jsonify({"status": "healthy", "service": "post_service"}), 200

@app.route('/posts', methods=['POST'])
def create_post():
    session_id = request.headers.get('Session-ID')
    
    # Validate session
    session_data = validate_session(session_id)
    if not session_data.get('valid'):
        return jsonify({"error": "Authentication required"}), 401
    
    data = request.get_json()
    
    if not data or not data.get('content'):
        return jsonify({"error": "Post content is required"}), 400
    
    # Create new post
    post_id = str(uuid.uuid4())
    posts[post_id] = {
        'id': post_id,
        'user_id': session_data['user_id'],
        'username': session_data['username'],
        'content': data['content'],
        'image_url': data.get('image_url', ''),
        'created_at': datetime.now().isoformat(),
        'likes': 0,
        'liked_by': [],
        'comments_count': 0
    }
    
    return jsonify({
        "message": "Post created successfully",
        "post": posts[post_id]
    }), 201

@app.route('/posts', methods=['GET'])
def get_posts():
    # Get posts with optional filtering
    user_id = request.args.get('user_id')
    limit = int(request.args.get('limit', 50))
    
    filtered_posts = []
    
    for post_id, post in posts.items():
        if user_id and post['user_id'] != user_id:
            continue
        filtered_posts.append(post)
    
    # Sort by creation time (newest first)
    filtered_posts.sort(key=lambda x: x['created_at'], reverse=True)
    
    # Apply limit
    filtered_posts = filtered_posts[:limit]
    
    return jsonify({"posts": filtered_posts}), 200

@app.route('/posts/<post_id>', methods=['GET'])
def get_post(post_id):
    if post_id not in posts:
        return jsonify({"error": "Post not found"}), 404
    
    return jsonify(posts[post_id]), 200

@app.route('/posts/<post_id>', methods=['DELETE'])
def delete_post(post_id):
    session_id = request.headers.get('Session-ID')
    
    # Validate session
    session_data = validate_session(session_id)
    if not session_data.get('valid'):
        return jsonify({"error": "Authentication required"}), 401
    
    if post_id not in posts:
        return jsonify({"error": "Post not found"}), 404
    
    # Check if user owns the post
    if posts[post_id]['user_id'] != session_data['user_id']:
        return jsonify({"error": "Unauthorized to delete this post"}), 403
    
    deleted_post = posts.pop(post_id)
    
    return jsonify({
        "message": "Post deleted successfully",
        "post": deleted_post
    }), 200

@app.route('/posts/<post_id>/like', methods=['POST'])
def like_post(post_id):
    session_id = request.headers.get('Session-ID')
    
    # Validate session
    session_data = validate_session(session_id)
    if not session_data.get('valid'):
        return jsonify({"error": "Authentication required"}), 401
    
    if post_id not in posts:
        return jsonify({"error": "Post not found"}), 404
    
    user_id = session_data['user_id']
    post = posts[post_id]
    
    # Toggle like
    if user_id in post['liked_by']:
        post['liked_by'].remove(user_id)
        post['likes'] -= 1
        action = "unliked"
    else:
        post['liked_by'].append(user_id)
        post['likes'] += 1
        action = "liked"
        
        # Send notification if this is a new like and not user's own post
        if post['user_id'] != user_id:
            try:
                notification_data = {
                    'user_id': post['user_id'],
                    'type': 'like',
                    'message': f'{session_data["username"]} liked your post',
                    'from_user_id': user_id,
                    'from_username': session_data['username'],
                    'post_id': post_id
                }
                requests.post('http://localhost:5005/notifications', json=notification_data)
            except:
                pass  # Don't fail if notification service is down
    
    return jsonify({
        "message": f"Post {action} successfully",
        "post": post
    }), 200

@app.route('/posts/<post_id>/comments', methods=['GET'])
def get_comments(post_id):
    if post_id not in posts:
        return jsonify({"error": "Post not found"}), 404
    
    post_comments = []
    for comment_id, comment in comments.items():
        if comment['post_id'] == post_id:
            post_comments.append(comment)
    
    # Sort by creation time (oldest first for comments)
    post_comments.sort(key=lambda x: x['created_at'])
    
    return jsonify({"comments": post_comments}), 200

@app.route('/posts/<post_id>/comments', methods=['POST'])
def add_comment(post_id):
    session_id = request.headers.get('Session-ID')
    
    # Validate session
    session_data = validate_session(session_id)
    if not session_data.get('valid'):
        return jsonify({"error": "Authentication required"}), 401
    
    if post_id not in posts:
        return jsonify({"error": "Post not found"}), 404
    
    data = request.get_json()
    
    if not data or not data.get('content'):
        return jsonify({"error": "Comment content is required"}), 400
    
    # Create new comment
    comment_id = str(uuid.uuid4())
    comments[comment_id] = {
        'id': comment_id,
        'post_id': post_id,
        'user_id': session_data['user_id'],
        'username': session_data['username'],
        'content': data['content'],
        'created_at': datetime.now().isoformat()
    }
    
    # Update comment count on post
    posts[post_id]['comments_count'] += 1
    
    return jsonify({
        "message": "Comment added successfully",
        "comment": comments[comment_id]
    }), 201

@app.route('/posts/<post_id>/comments/<comment_id>', methods=['DELETE'])
def delete_comment(post_id, comment_id):
    session_id = request.headers.get('Session-ID')
    
    # Validate session
    session_data = validate_session(session_id)
    if not session_data.get('valid'):
        return jsonify({"error": "Authentication required"}), 401
    
    if comment_id not in comments:
        return jsonify({"error": "Comment not found"}), 404
    
    comment = comments[comment_id]
    
    # Check if user owns the comment or the post
    if (comment['user_id'] != session_data['user_id'] and 
        posts.get(post_id, {}).get('user_id') != session_data['user_id']):
        return jsonify({"error": "Unauthorized to delete this comment"}), 403
    
    deleted_comment = comments.pop(comment_id)
    
    # Update comment count on post
    if post_id in posts:
        posts[post_id]['comments_count'] = max(0, posts[post_id]['comments_count'] - 1)
    
    return jsonify({
        "message": "Comment deleted successfully",
        "comment": deleted_comment
    }), 200

@app.route('/posts/feed', methods=['GET'])
def get_feed():
    session_id = request.headers.get('Session-ID')
    
    # Validate session
    session_data = validate_session(session_id)
    if not session_data.get('valid'):
        return jsonify({"error": "Authentication required"}), 401
    
    user_id = session_data['user_id']
    limit = int(request.args.get('limit', 20))
    
    # Get following list from follow service
    try:
        response = requests.get(
            f"http://localhost:5003/following/{user_id}",
            headers={"Session-ID": session_id}
        )
        following_data = response.json() if response.status_code == 200 else {"following": []}
        following_ids = [user['user_id'] for user in following_data.get('following', [])]
    except:
        following_ids = []
    
    # Include user's own posts
    following_ids.append(user_id)
    
    # Get posts from following and self
    feed_posts = []
    for post_id, post in posts.items():
        if post['user_id'] in following_ids:
            feed_posts.append(post)
    
    # Sort by creation time (newest first)
    feed_posts.sort(key=lambda x: x['created_at'], reverse=True)
    
    # Apply limit
    feed_posts = feed_posts[:limit]
    
    return jsonify({"posts": feed_posts}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)