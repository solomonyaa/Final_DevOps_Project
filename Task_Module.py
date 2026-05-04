from db import db
from datetime import datetime
from enum import Enum


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Category(Enum):
    PERSONAL = "personal"
    WORK = "work"
    SHOPPING = "shopping"


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(30), nullable=False)
    details = db.Column(db.String(500), nullable=False)
    due_date = db.Column(db.String(10), nullable=False)
    is_complete = db.Column(db.Boolean, default=False)
    category = db.Column(db.String(20), nullable=False)
    priority = db.Column(db.String(10), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    date_format = "%d/%m/%Y"

    def __init__(self, title, details, due_date, category, priority, user_id):
        if not isinstance(title, str):
            raise TypeError("Title must be a string")
        if not isinstance(details, str):
            raise TypeError("Details must be a string")
        if len(title) > 30:
            raise ValueError("Title exceeds max length of 30 characters")
        if len(details) > 500:
            raise ValueError("Details exceeds max length of 500 characters")

        try:
            datetime.strptime(due_date, self.date_format)
        except ValueError:
            raise ValueError(f"Incorrect format of due date: {due_date}")

        self.title = title
        self.details = details
        self.due_date = due_date
        self.category = Category(category).value
        self.priority = Priority(priority).value
        self.user_id = user_id

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "details": self.details,
            "due_date": self.due_date,
            "is_complete": self.is_complete,
            "category": self.category,
            "priority": self.priority,
            "user_id": self.user_id
        }
