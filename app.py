from flask import Flask, render_template, redirect, url_for, request

app = Flask(__name__)

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
        username = request.form.get('username')
        password = request.form.get('password')
        for user in users:
            if user['username'] == username and user['password'] == password:
                return redirect(url_for('welcome', username=user['username']))
        return "Invalid username or password. Please try again."
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        # You might want to add validation and error handling for registration here
        users.append({"username": username, "email": email, "password": password})
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/welcome/<username>')
def welcome(username):
    return render_template('welcome.html', username=username)

if __name__ == '__main__':
    app.run(debug=True)
