from flask import Flask, request, jsonify
from Task_Module import Task, Category, Priority
from User_Module import User
from datetime import datetime
from typing import Dict
from openai import OpenAI
import functools

app = Flask(__name__)
tasks: Dict[int, Task] = {}
users: Dict[str, User] = {}
_openai_client = None


def get_openai_client():
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI()
    return _openai_client


def require_auth(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username not in users:
            return jsonify({"error": "Authentication required"}), 401
        user = users[auth.username]
        if not user.check_password(auth.password):
            return jsonify({"error": "Invalid username or password"}), 401
        return f(*args, **kwargs, current_user=user)
    return wrapper


def is_valid_date(date_str, fmt=Task.date_format):
    try:
        datetime.strptime(date_str, fmt)
        return True
    except ValueError:
        return False


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200


@app.route('/users/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid or missing JSON"}), 400
    if 'username' not in data or 'password' not in data:
        return jsonify({"error": "Missing required fields: username, password"}), 400
    if data['username'] in users:
        return jsonify({"error": "Username already exists"}), 409
    try:
        user = User(data['username'], data['password'])
    except (TypeError, ValueError) as e:
        return jsonify({"error": str(e)}), 400
    users[user.username] = user
    return jsonify(user.to_dict()), 201


@app.route('/tasks', methods=['POST'])
@require_auth
def create_task(current_user):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid or missing JSON"}), 400

    required = ['title', 'details', 'due_date', 'category', 'priority']
    missing = []
    for f in required:
        if f not in data:
            missing.append(f)
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400

    try:
        new_task = Task(
            data['title'],
            data['details'],
            data['due_date'],
            data['category'],
            data['priority'],
            current_user.id
        )
    except (TypeError, ValueError) as e:
        return jsonify({"error": str(e)}), 400

    tasks[new_task.id] = new_task
    return jsonify(new_task.to_dict()), 201


@app.route('/tasks', methods=['GET'])
@require_auth
def get_tasks(current_user):
    filtered_tasks = [t for t in tasks.values() if t.user_id == current_user.id]

    category = request.args.get('category')
    priority = request.args.get('priority')
    is_complete = request.args.get('is_complete')

    if category:
        filtered_tasks = [t for t in filtered_tasks if t.category.value == category]
    if priority:
        filtered_tasks = [t for t in filtered_tasks if t.priority.value == priority]
    if is_complete is not None:
        complete_bool = is_complete.lower() == 'true'
        filtered_tasks = [t for t in filtered_tasks if t.is_complete == complete_bool]

    if not filtered_tasks:
        return jsonify({"error": "No tasks found"}), 404

    return jsonify([t.to_dict() for t in sorted(filtered_tasks)]), 200


@app.route('/task/<int:task_id>', methods=['GET'])
@require_auth
def get_task(task_id, current_user):
    task = tasks.get(task_id)
    if not task or task.user_id != current_user.id:
        return jsonify({"error": "Task not found"}), 404

    return jsonify(task.to_dict()), 200


@app.route('/task/<int:task_id>', methods=['PATCH'])
@require_auth
def edit_task(task_id, current_user):
    task = tasks.get(task_id)
    if not task or task.user_id != current_user.id:
        return jsonify({"error": "Task not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid or missing JSON"}), 400

    editable_fields = ["title", "details", "due_date", "category", "priority"]
    for field in editable_fields:
        if field in data:
            if field == "due_date":
                if not is_valid_date(data["due_date"]):
                    return jsonify({"error": "Invalid date format, expected DD/MM/YYYY"}), 400
                setattr(task, field, data[field])
            elif field == "category":
                try:
                    setattr(task, field, Category(data[field]))
                except ValueError:
                    return jsonify({"error": f"Invalid category: {data[field]}"}), 400
            elif field == "priority":
                try:
                    setattr(task, field, Priority(data[field]))
                except ValueError:
                    return jsonify({"error": f"Invalid priority: {data[field]}"}), 400
            else:
                setattr(task, field, data[field])

    return jsonify({"success": True, "task": task.to_dict()}), 200


@app.route('/task/<int:task_id>', methods=['DELETE'])
@require_auth
def delete_task(task_id, current_user):
    task = tasks.get(task_id)
    if not task or task.user_id != current_user.id:
        return jsonify({"error": "Task not found"}), 404

    tasks.pop(task_id)
    return jsonify({"success": True}), 200


@app.route('/task/<int:task_id>/complete', methods=['PATCH'])
@require_auth
def set_task_complete(task_id, current_user):
    task = tasks.get(task_id)
    if not task or task.user_id != current_user.id:
        return jsonify({"error": "Task not found"}), 404

    data = request.get_json()
    if not data or 'is_complete' not in data:
        return jsonify({"error": "Missing required field: is_complete"}), 400

    if not isinstance(data['is_complete'], bool):
        return jsonify({"error": "is_complete must be a boolean"}), 400

    task.is_complete = data['is_complete']
    return jsonify({"success": True, "task": task.to_dict()}), 200


@app.route('/task/<int:task_id>/ask', methods=['POST'])
@require_auth
def ask_about_task(task_id, current_user):
    task = tasks.get(task_id)
    if not task or task.user_id != current_user.id:
        return jsonify({"error": "Task not found"}), 404

    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify({"error": "Missing required field: question"}), 400

    system_prompt = (
        "You are a productivity assistant. "
        "The user will ask you about a task they need to complete. "
        "Give practical, concise advice on how to best do it."
    )

    user_prompt = (
        f"Task: {task.title}\n"
        f"Details: {task.details}\n"
        f"Due date: {task.due_date}\n"
        f"Priority: {task.priority.value}\n"
        f"Category: {task.category.value}\n\n"
        f"Question: {data['question']}"
    )

    response = get_openai_client().chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.5
    )

    answer = response.choices[0].message.content
    return jsonify({"task_id": task_id, "question": data['question'], "answer": answer}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
