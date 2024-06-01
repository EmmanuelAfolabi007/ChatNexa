import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True
    SESSION_TYPE = 'filesystem'  # Use filesystem-based session storage
    SESSION_FILE_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'flask_session')  # Set custom session directory

# Ensure the directory exists
if not os.path.exists(Config.SESSION_FILE_DIR):
    os.makedirs(Config.SESSION_FILE_DIR)
