# Import necessary modules
from flask import Flask, render_template, redirect, url_for, request, session, abort
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from config import Config
import bcrypt

# Create Flask app and configure it
app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# Import User model
from models import User

# Initialize Flask Session
Session(app)

# Import Flask Migrate for database migrations
from flask_migrate import Migrate
migrate = Migrate(app, db)

# Function to clear session before request
@app.before_request
def clear_session():
    if 'user_id' not in session and request.endpoint not in ['login', 'register']:
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
    
    other_users = User.query.filter(User.id != current_user_id).all()
    
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
            return "Invalid username or password. Please try again."

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
            return "Username or email already exists. Please choose a different one."

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

# Run the application
if __name__ == '__main__':
    app.run(debug=True)
