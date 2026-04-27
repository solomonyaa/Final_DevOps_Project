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


class Task:
    static_id = 1
    date_format = "%d/%m/%Y"

    def __init__(self, title, details, due_date, category, priority):
        if not isinstance(title, str):
            raise TypeError("Title must be a string")
        if not isinstance(details, str):
            raise TypeError("Details must be a string")
        try:
            datetime.strptime(due_date, Task.date_format)
        except ValueError:
            raise ValueError(f"Incorrect format of due date: {due_date}")

        self.id = Task.static_id
        Task.static_id += 1
        self.is_complete = False
        self.title = title
        self.details = details
        self.due_date = due_date
        self.category = Category(category)
        self.priority = Priority(priority)

    def __str__(self):
        return (
            f"Task ID: {self.id}, "
            f"Title: {self.title}, "
            f"Details: {self.details}, "
            f"Due Date: {self.due_date}, "
            f"Category: {self.category.name}, "
            f"Priority: {self.priority.name}"
        )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "details": self.details,
            "due_date": self.due_date,
            "is_complete": self.is_complete,
            "category": self.category.value,
            "priority": self.priority.value
        }

    def __lt__(self, other):
        if not isinstance(other, Task):
            return NotImplemented
        return (datetime.strptime(self.due_date, Task.date_format) <
                datetime.strptime(other.due_date, Task.date_format))

    def __gt__(self, other):
        if not isinstance(other, Task):
            return NotImplemented
        return (datetime.strptime(self.due_date, Task.date_format) >
                datetime.strptime(other.due_date, Task.date_format))

    def __eq__(self, other):
        if not isinstance(other, Task):
            return False
        return self.id == other.id
