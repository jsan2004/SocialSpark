from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_cors import CORS
import requests
import os
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'
CORS(app)

# API Gateway URL
API_BASE_URL = "http://localhost:5004/api"

# Configure upload settings
UPLOAD_FOLDER = 'static/uploads/posts'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def make_api_request(endpoint, method='GET', data=None, params=None):
    """Make request to API Gateway"""
    url = f"{API_BASE_URL}{endpoint}"
    headers = {}
    
    # Add session ID if available
    if 'session_id' in session:
        headers['Session-ID'] = session['session_id']
    
    try:
        response = None
        if method == 'GET':
            response = requests.get(url, headers=headers, params=params)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=data)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        
        if response and response.status_code < 400:
            try:
                return response.json(), response.status_code
            except:
                return {"message": "Success"}, response.status_code
        elif response:
            try:
                return response.json(), response.status_code
            except:
                return {"error": "Request failed"}, response.status_code
        else:
            return {"error": "Invalid method"}, 405
    except:
        return {"error": "Service unavailable"}, 503

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get user's feed
    feed_data, status_code = make_api_request('/posts/feed')
    posts = feed_data.get('posts', []) if status_code == 200 else []
    
    # Get notifications count
    notifications_data, _ = make_api_request('/notifications/unread_count')
    unread_count = notifications_data.get('unread_count', 0)
    
    return render_template('index.html', posts=posts, unread_count=unread_count)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        data = {'username': username, 'password': password}
        response_data, status_code = make_api_request('/login', 'POST', data)
        
        if status_code == 200:
            session['session_id'] = response_data['session_id']
            session['user_id'] = response_data['user_id']
            session['username'] = response_data['username']
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash(response_data.get('error', 'Login failed'), 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        full_name = request.form.get('full_name', '')
        
        data = {
            'username': username,
            'email': email,
            'password': password,
            'full_name': full_name
        }
        
        response_data, status_code = make_api_request('/register', 'POST', data)
        
        if status_code == 201:
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash(response_data.get('error', 'Registration failed'), 'error')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    make_api_request('/logout', 'POST')
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/profile')
@app.route('/profile/<user_id>')
def profile(user_id=None):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    target_user_id = user_id or session['user_id']
    
    # Get user profile
    profile_data, status_code = make_api_request(f'/profile/{target_user_id}')
    if status_code != 200:
        flash('User not found', 'error')
        return redirect(url_for('index'))
    
    user_profile = profile_data
    
    # Get user's posts
    posts_data, _ = make_api_request(f'/posts?user_id={target_user_id}')
    user_posts = posts_data.get('posts', [])
    
    # Get follow status and stats if viewing another user's profile
    follow_status = None
    follow_stats = None
    if target_user_id != session['user_id']:
        status_data, _ = make_api_request(f'/follow_status/{target_user_id}')
        follow_status = status_data
    
    # Get follow stats for this user
    stats_data, _ = make_api_request(f'/stats/{target_user_id}')
    follow_stats = stats_data
    
    return render_template('profile.html', 
                         user_profile=user_profile, 
                         user_posts=user_posts,
                         follow_status=follow_status,
                         follow_stats=follow_stats,
                         is_own_profile=(target_user_id == session['user_id']))

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'GET':
        # Get current user profile data
        profile_data, status_code = make_api_request('/profile/edit', 'GET')
        if status_code == 200:
            return render_template('edit_profile.html', user=profile_data)
        else:
            flash('Failed to load profile data', 'error')
            return redirect(url_for('profile'))
    
    elif request.method == 'POST':
        # Update profile
        data = {
            'username': request.form.get('username'),
            'bio': request.form.get('bio'),
            'full_name': request.form.get('full_name')
        }
        
        response_data, status_code = make_api_request('/profile/edit', 'PUT', data)
        
        if status_code == 200:
            # Update session username if it changed
            if 'username' in data and data['username']:
                session['username'] = data['username']
            flash('Profile updated successfully!', 'success')
        else:
            flash(response_data.get('error', 'Failed to update profile'), 'error')
        
        return redirect(url_for('profile'))

@app.route('/create_post', methods=['POST'])
def create_post():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    content = request.form['content']
    
    # Handle image upload
    image_url = ''
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(f"{session['user_id']}_{uuid.uuid4()}.{file.filename.rsplit('.', 1)[1].lower()}")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            image_url = f"/static/uploads/posts/{filename}"
    
    data = {'content': content, 'image_url': image_url}
    
    response_data, status_code = make_api_request('/posts', 'POST', data)
    
    if status_code == 201:
        flash('Post created successfully!', 'success')
    else:
        flash(response_data.get('error', 'Failed to create post'), 'error')
    
    return redirect(url_for('index'))

@app.route('/delete_post/<post_id>')
def delete_post(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    response_data, status_code = make_api_request(f'/posts/{post_id}', 'DELETE')
    
    if status_code == 200:
        flash('Post deleted successfully!', 'success')
    else:
        flash(response_data.get('error', 'Failed to delete post'), 'error')
    
    return redirect(url_for('index'))

@app.route('/like_post/<post_id>')
def like_post(post_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    response_data, status_code = make_api_request(f'/posts/{post_id}/like', 'POST')
    
    if status_code == 200:
        return jsonify({'success': True, 'post': response_data['post']})
    else:
        return jsonify({'error': response_data.get('error', 'Failed to like post')}), status_code

@app.route('/search_users')
def search_users():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    query = request.args.get('q', '')
    users_data, _ = make_api_request(f'/users/search?q={query}')
    users = users_data.get('users', [])
    
    return render_template('search_users.html', users=users, query=query)


@app.route('/follow_user/<user_id>')
def follow_user(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    data = {'user_id': user_id}
    response_data, status_code = make_api_request('/follow', 'POST', data)
    
    if status_code == 201:
        flash('Successfully followed user!', 'success')
    else:
        flash(response_data.get('error', 'Failed to follow user'), 'error')
    
    return redirect(url_for('profile', user_id=user_id))

@app.route('/unfollow_user/<user_id>')
def unfollow_user(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    data = {'user_id': user_id}
    response_data, status_code = make_api_request('/unfollow', 'POST', data)
    
    if status_code == 200:
        flash('Successfully unfollowed user!', 'success')
    else:
        flash(response_data.get('error', 'Failed to unfollow user'), 'error')
    
    return redirect(url_for('profile', user_id=user_id))

@app.route('/notifications')
def notifications():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get notifications
    notifications_data, _ = make_api_request('/notifications')
    user_notifications = notifications_data.get('notifications', [])
    
    return render_template('notifications.html', notifications=user_notifications)

@app.route('/add_comment/<post_id>', methods=['POST'])
def add_comment(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    content = request.form['content']
    data = {'content': content}
    
    response_data, status_code = make_api_request(f'/posts/{post_id}/comments', 'POST', data)
    
    if status_code == 201:
        flash('Comment added successfully!', 'success')
    else:
        flash(response_data.get('error', 'Failed to add comment'), 'error')
    
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)