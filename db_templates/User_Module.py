from db import db
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    tasks = db.relationship('Task', backref='user', lazy=True)

    def __init__(self, username, password):
        if not isinstance(username, str) or not username.strip():
            raise ValueError("Username must be a non-empty string")
        if not isinstance(password, str) or len(password) < 6:
            raise ValueError("Password must be at least 6 characters")

        self.username = username
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username
        }
