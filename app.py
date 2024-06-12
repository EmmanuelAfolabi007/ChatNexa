from flask import Flask, render_template, redirect, url_for, request, session, abort, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from markupsafe import Markup
from config import Config
from flask_socketio import SocketIO, send, emit, join_room
from datetime import datetime
import bcrypt
from werkzeug.utils import secure_filename
from models import db, User, Friendship, Message
from forms import ProfilePictureForm
import os

# Import forms
from forms import ProfilePictureForm

# Create Flask app and configure it
app = Flask(__name__)
app.config.from_object(Config)
socketio = SocketIO(app)

db.init_app(app)

# Initialize Flask Session
Session(app)

# Import Flask Migrate for database migrations
from flask_migrate import Migrate
migrate = Migrate(app, db)

# Function to send notifications to users
def send_notification(user_id, message):
    socketio.emit('notification', {'message': message}, room=f"user_{user_id}")

# Function to clear session before request
@app.before_request
def clear_session():
    if 'user_id' not in session and request.endpoint not in ['login', 'register', 'static']:
        session.clear()

# Route for home page
@app.route('/')
@app.route('/index')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    current_user_id = session.get('user_id')
    current_user = User.query.get(current_user_id)
    
    if not current_user:
        session.clear()
        return redirect(url_for('login'))
    
    other_users = User.query.filter(User.id != current_user_id).paginate(page=1, per_page=10)

    return render_template('index.html', current_user=current_user, other_users=other_users)

# Route for user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('welcome', username=user.username))
        else:
            flash("Invalid username or password. Please try again.")

    return render_template('login.html')

# Route for user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if the username or email already exists in the database
        existing_user = User.query.filter_by(username=username).first() or \
                        User.query.filter_by(email=email).first()
        if existing_user:
            flash("Username or email already exists. Please choose a different one.")
            return redirect(url_for('register'))

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Create a new User object with the hashed password and add it to the database
        new_user = User(username=username, email=email, password=hashed_password.decode('utf-8'))
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

# Route for welcoming user
@app.route('/welcome/<username>')
def welcome(username):
    if 'user_id' not in session or username != session.get('username'):
        abort(401)
    
    return render_template('welcome.html', username=username)

# Route for user logout
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

# Route for user profile page
@app.route('/profile/<int:user_id>', methods=['GET', 'POST'])
def profile(user_id):
    user = User.query.get_or_404(user_id)
    form = ProfilePictureForm(request.form, obj=user)  # Assuming you have a ProfileForm with fields for bio, location, interests, and social_media_links
    if request.method == 'POST' and form.validate():
        form.populate_obj(user)
        if form.profile_picture.data:
            filename = secure_filename(form.profile_picture.data.filename)
            form.profile_picture.data.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            user.profile_picture = filename
        db.session.commit()
        flash('Profile updated successfully!')
        return redirect(url_for('profile', user_id=user_id))
    return render_template('profile.html', user=user, form=form)

# Route to send friend request
@app.route('/send_friend_request/<int:friend_id>', methods=['POST'])
def send_friend_request(friend_id):
    if 'user_id' not in session:
        abort(401)
    
    user_id = session['user_id']
    existing_friendship = Friendship.query.filter(
        (Friendship.user_id == user_id) & (Friendship.friend_id == friend_id) |
        (Friendship.user_id == friend_id) & (Friendship.friend_id == user_id)
    ).first()

    if existing_friendship:
        flash('Friend request already sent or you are already friends.')
        return redirect(url_for('profile', user_id=friend_id))

    new_friendship = Friendship(user_id=user_id, friend_id=friend_id, status='pending')
    db.session.add(new_friendship)
    db.session.commit()
    flash('Friend request sent.')
    
    # Emit notification to the friend
    send_notification(friend_id, 'You received a friend request!')

    return redirect(url_for('profile', user_id=friend_id))

# Route to accept friend request
@app.route('/accept_friend_request/<int:request_id>', methods=['POST'])
def accept_friend_request(request_id):
    if 'user_id' not in session:
        abort(401)

    friendship = Friendship.query.get_or_404(request_id)
    if friendship.friend_id != session['user_id']:
        abort(403)

    friendship.status = 'accepted'
    db.session.commit()
    flash('Friend request accepted.')
    
    # Emit notification to the requester
    send_notification(friendship.user_id, 'Your friend request was accepted.')

    return redirect(url_for('profile', user_id=friendship.user_id))

# Route to reject friend request
@app.route('/reject_friend_request/<int:request_id>', methods=['POST'])
def reject_friend_request(request_id):
    if 'user_id' not in session:
        abort(401)

    friendship = Friendship.query.get_or_404(request_id)
    if friendship.friend_id != session['user_id']:
        abort(403)

    db.session.delete(friendship)
    db.session.commit()
    flash('Friend request rejected.')
    
    # Emit notification to the requester
    send_notification(friendship.user_id, 'Your friend request was rejected.')

    return redirect(url_for('profile', user_id=friendship.user_id))

# Route for chat
@app.route('/chat/<int:recipient_id>', methods=['GET', 'POST'])
def chat(recipient_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Ensure only authenticated users can access the chat feature
    if request.method == 'POST':
        content = request.form.get('content')
        if not content:
            flash('Message content cannot be empty.')

        # Authorization: Verify users have permission to send messages

        recipient = User.query.get(recipient_id)
        if not recipient:
            abort(404)

        sender_id = session['user_id']
        message = Message(sender_id=sender_id, recipient_id=recipient_id, content=content, timestamp=datetime.utcnow())
        db.session.add(message)
        db.session.commit()

        # Emit the message to the recipient via WebSocket
        socketio.emit('message', {
            'sender_id': sender_id,
            'recipient_id': recipient_id,
            'sender': session['username'],
            'content': content,
            'timestamp': message.timestamp.isoformat()
        }, room=f"user_{recipient_id}")

    # Retrieve chat history with the recipient
    messages = Message.query.filter(
        ((Message.sender_id == session['user_id']) & (Message.recipient_id == recipient_id)) |
        ((Message.sender_id == recipient_id) & (Message.recipient_id == session['user_id']))
    ).order_by(Message.timestamp.asc()).all()

    return render_template('chat.html', recipient_id=recipient_id, messages=messages)

# Route to fetch messages with a specific recipient via AJAX
@app.route('/messages/<int:recipient_id>')
def get_messages(recipient_id):
    if 'user_id' not in session:
        return abort(401)

    current_user_id = session['user_id']
    messages = Message.query.filter(
        ((Message.sender_id == current_user_id) & (Message.recipient_id == recipient_id)) |
        ((Message.sender_id == recipient_id) & (Message.recipient_id == current_user_id))
    ).order_by(Message.timestamp.asc()).all()

    return jsonify([{
        'sender': message.sender.username,
        'content': message.content,
        'timestamp': message.timestamp.isoformat()
    } for message in messages])

@socketio.on('message')
def handle_message(data):
    # Handle incoming messages
    print('Received message:', data)
    # Broadcast the message to all connected clients
    send(data, broadcast=True)
    
# Backend Implementation
@app.route('/search')
def search():
    query = request.args.get('q')  # Get the search query from the request parameters

    # Dummy search results for demonstration purposes
    results = [
        {'type': 'user', 'id': 1, 'name': 'John Doe'},
        {'type': 'user', 'id': 2, 'name': 'Alice Smith'},
        {'type': 'group', 'id': 1, 'name': 'Travel Enthusiasts'},
        {'type': 'content', 'id': 1, 'title': 'Best Travel Destinations'}
    ]

    return jsonify(results)

# Your code using Markup goes here
safe_string = Markup("<strong>Safe HTML</strong>")
print(safe_string)

# Run the application
if __name__ == '__main__':
    socketio.run(app, debug=True)

