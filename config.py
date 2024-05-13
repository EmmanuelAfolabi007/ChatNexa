import os

class Config:
    # Set the secret key to protect session data
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'

    # SQLAlchemy configuration for SQLite
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Debug mode setting
    DEBUG = True
