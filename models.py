from app import db  # Import db from app

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)  # Added nullable=False
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)  # Added nullable=False
    password = db.Column(db.String(128), nullable=False)  # Added nullable=False

    def __repr__(self):
        return '<User {}>'.format(self.username)
