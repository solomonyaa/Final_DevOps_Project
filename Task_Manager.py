from flask import Flask, request, jsonify
from Task_Module import Task, Category, Priority
from datetime import datetime
from typing import Dict

app = Flask(__name__)

tasks: Dict[int, Task] = {}


def is_valid_date(date_str, fmt=Task.date_format):
    try:
        datetime.strptime(date_str, fmt)
        return True
    except ValueError:
        return False


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200


@app.route('/tasks', methods=['POST'])
def create_task():
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
            data['priority']
        )
    except (TypeError, ValueError) as e:
        return jsonify({"error": str(e)}), 400

    tasks[new_task.id] = new_task
    return jsonify(new_task.to_dict()), 201


@app.route('/tasks', methods=['GET'])
def get_tasks():
    filtered_tasks = list(tasks.values())

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
def get_task(task_id):
    if task_id not in tasks:
        return jsonify({"error": "Task not found"}), 404

    return jsonify(tasks[task_id].to_dict()), 200


@app.route('/task/<int:task_id>', methods=['PATCH'])
def edit_task(task_id):
    if task_id not in tasks:
        return jsonify({"error": "Task not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid or missing JSON"}), 400

    task = tasks[task_id]

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
def delete_task(task_id):
    if task_id not in tasks:
        return jsonify({"error": "Task not found"}), 404

    tasks.pop(task_id)
    return jsonify({"success": True}), 200


@app.route('/task/<int:task_id>/complete', methods=['PATCH'])
def set_task_complete(task_id):
    if task_id not in tasks:
        return jsonify({"error": "Task not found"}), 404

    data = request.get_json()
    if not data or 'is_complete' not in data:
        return jsonify({"error": "Missing required field: is_complete"}), 400

    if not isinstance(data['is_complete'], bool):
        return jsonify({"error": "is_complete must be a boolean"}), 400

    tasks[task_id].is_complete = data['is_complete']
    return jsonify({"success": True, "task": tasks[task_id].to_dict()}), 200


if __name__ == '__main__':
    app.run(debug=True)
