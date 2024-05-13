from flask import Flask, render_template, redirect, url_for, request, session, abort
from flask_sqlalchemy import SQLAlchemy
from config import Config
import bcrypt

app = Flask(__name__)
app.config.from_object(Config)

# Initialize the database
db = SQLAlchemy(app)

# Simulated user data (replace with your database logic)
users = [
    {"username": "User1", "email": "user1@example.com", "password": "password1"},
    {"username": "User2", "email": "user2@example.com", "password": "password2"}
]

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        from models import User  # Import inside the function to avoid circular imports
        username = request.form.get('username')
        password = request.form.get('password')

        # Query the database for the user
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            # Store user session information (you may want to use Flask-Login for more advanced session management)
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('welcome', username=user.username))

        return "Invalid username or password. Please try again."

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        from models import User  # Import inside the function to avoid circular imports
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

@app.route('/welcome/<username>')
def welcome(username):
    # Check if user is authenticated
    if 'user_id' not in session:
        abort(401)  # Unauthorized
        
    # Retrieve the user's information from session
    if username != session.get('username'):
        abort(403)  # Forbidden
        
    return render_template('welcome.html', username=username)

# Logout route
@app.route('/logout')
def logout():
    # Remove user session data
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
