from flask import Flask, request, jsonify
from db import db, init_db
from Task_Module import Task, Category, Priority
from User_Module import User
from datetime import datetime
from openai import OpenAI
import functools


app = Flask(__name__)
init_db(app)

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
        if not auth:
            return jsonify({"error": "Authentication required"}), 401
        user = User.query.filter_by(username=auth.username).first()
        if not user or not user.check_password(auth.password):
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
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "Username already exists"}), 409
    try:
        user = User(data['username'], data['password'])
    except (TypeError, ValueError) as e:
        return jsonify({"error": str(e)}), 400
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201


@app.route('/tasks', methods=['POST'])
@require_auth
def create_task(current_user):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid or missing JSON"}), 400
    required = ['title', 'details', 'due_date', 'category', 'priority']
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400
    try:
        task = Task(data['title'], data['details'], data['due_date'],
                    data['category'], data['priority'], current_user.id)
    except (TypeError, ValueError) as e:
        return jsonify({"error": str(e)}), 400
    db.session.add(task)
    db.session.commit()
    return jsonify(task.to_dict()), 201


@app.route('/tasks', methods=['GET'])
@require_auth
def get_tasks(current_user):
    query = Task.query.filter_by(user_id=current_user.id)
    if request.args.get('category'):
        query = query.filter_by(category=request.args.get('category'))
    if request.args.get('priority'):
        query = query.filter_by(priority=request.args.get('priority'))
    if request.args.get('is_complete') is not None:
        complete_bool = request.args.get('is_complete').lower() == 'true'
        query = query.filter_by(is_complete=complete_bool)
    tasks = query.all()
    if not tasks:
        return jsonify({"error": "No tasks found"}), 404
    return jsonify([t.to_dict() for t in tasks]), 200


@app.route('/task/<int:task_id>', methods=['GET'])
@require_auth
def get_task(task_id, current_user):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task.to_dict()), 200


@app.route('/task/<int:task_id>', methods=['PATCH'])
@require_auth
def edit_task(task_id, current_user):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
        return jsonify({"error": "Task not found"}), 404
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid or missing JSON"}), 400
    if 'due_date' in data and not is_valid_date(data['due_date']):
        return jsonify({"error": "Invalid date format, expected DD/MM/YYYY"}), 400
    for field in ['title', 'details', 'due_date']:
        if field in data:
            setattr(task, field, data[field])
    if 'category' in data:
        try:
            task.category = Category(data['category']).value
        except ValueError:
            return jsonify({"error": f"Invalid category: {data['category']}"}), 400
    if 'priority' in data:
        try:
            task.priority = Priority(data['priority']).value
        except ValueError:
            return jsonify({"error": f"Invalid priority: {data['priority']}"}), 400
    db.session.commit()
    return jsonify({"success": True, "task": task.to_dict()}), 200


@app.route('/task/<int:task_id>', methods=['DELETE'])
@require_auth
def delete_task(task_id, current_user):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()\

    if not task:
        return jsonify({"error": "Task not found"}), 404
    db.session.delete(task)
    db.session.commit()
    return jsonify({"success": True}), 200


@app.route('/task/<int:task_id>/complete', methods=['PATCH'])
@require_auth
def set_task_complete(task_id, current_user):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
        return jsonify({"error": "Task not found"}), 404
    data = request.get_json()
    if not data or 'is_complete' not in data:
        return jsonify({"error": "Missing required field: is_complete"}), 400
    if not isinstance(data['is_complete'], bool):
        return jsonify({"error": "is_complete must be a boolean"}), 400
    task.is_complete = data['is_complete']
    db.session.commit()
    return jsonify({"success": True, "task": task.to_dict()}), 200


@app.route('/task/<int:task_id>/ask', methods=['POST'])
@require_auth
def ask_about_task(task_id, current_user):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
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
        f"Priority: {task.priority}\n"
        f"Category: {task.category}\n\n"
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
