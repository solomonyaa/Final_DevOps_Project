from flask import Flask, request, jsonify, send_file
from Task_Module import Task, Category, Priority
from datetime import datetime

app = Flask(__name__)

t1 = Task("task1", "details1", "22/04/2026", Category.WORK.value, Priority.MEDIUM.value)
t3 = Task("task3", "details3", "01/05/2026", Category.SHOPPING.value, Priority.LOW.value)
t2 = Task("task2", "details2", "23/04/2026", Category.PERSONAL.value, Priority.HIGH.value)

tasks = {t1.id: t1, t3.id: t3, t2.id: t2}

for k in tasks.keys():
    print(tasks[k])


def is_valid_date(date_str, fmt="%d/%m/%Y"):  # Fix: format now matches Task_Module DD/MM/YYYY
    try:
        datetime.strptime(date_str, fmt)
        return True
    except ValueError:
        return False


@app.route('/new_task', methods=['POST'])
def create_new_task():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid or missing JSON"}), 400

    title = data.get('title')
    details = data.get('details')
    due_date = data.get('due_date')
    category = data.get('category')
    priority = data.get('priority')

    try:
        new_task = Task(title, details, due_date, category, priority)
    except (TypeError, ValueError) as e:
        return jsonify({"error": str(e)}), 400

    tasks[new_task.id] = new_task

    return jsonify(new_task.to_dict()), 201


@app.route('/del_task', methods=['POST'])
def delete_task():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid or missing JSON"}), 400

    task_id = data.get("task_id")
    if task_id is None:
        return jsonify({"error": "task_id is required"}), 400

    if task_id not in tasks:
        return jsonify({"error": "Task not found"}), 404

    tasks.pop(task_id)
    return jsonify({"success": True}), 200


@app.route('/edit_task', methods=['POST'])
def edit_task():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid or missing JSON"}), 400

    task_id = data.get("task_id")
    if task_id is None:
        return jsonify({"error": "task_id is required"}), 400

    if task_id not in tasks:
        return jsonify({"error": "Task not found"}), 404

    task = tasks[task_id]

    editable_fields = ["title", "details", "due_date", "category", "priority"]  # Fix: "task_name" -> "title"
    for field in editable_fields:
        if field in data:
            if field == "due_date":  # Fix: was "if due_date in data" inside every iteration
                if not is_valid_date(data["due_date"]):
                    return jsonify({"error": "Invalid date format, expected DD/MM/YYYY"}), 400
                setattr(task, field, data[field])
            elif field == "category":  # Fix: convert to Enum, not raw string
                try:
                    setattr(task, field, Category(data[field]))
                except ValueError:
                    return jsonify({"error": f"Invalid category: {data[field]}"}), 400
            elif field == "priority":  # Fix: convert to Enum, not raw string
                try:
                    setattr(task, field, Priority(data[field]))
                except ValueError:
                    return jsonify({"error": f"Invalid priority: {data[field]}"}), 400
            else:
                setattr(task, field, data[field])

    return jsonify({"success": True, "task": task.to_dict()}), 200  # Fix: vars(task) -> task.to_dict()


@app.route('/complete_task', methods=['POST'])
def complete_task():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid or missing JSON"}), 400

    task_id = data.get("task_id")
    if task_id is None:
        return jsonify({"error": "task_id is required"}), 400

    if task_id not in tasks:
        return jsonify({"error": "Task not found"}), 404

    tasks[task_id].is_complete = True
    return jsonify({"success": True}), 200


@app.route('/uncomplete_task', methods=['POST'])
def uncomplete_task():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid or missing JSON"}), 400

    task_id = data.get("task_id")
    if task_id is None:
        return jsonify({"error": "task_id is required"}), 400

    if task_id not in tasks:
        return jsonify({"error": "Task not found"}), 404

    tasks[task_id].is_complete = False
    return jsonify({"success": True}), 200


@app.route('/all', methods=['GET'])
def get_all_tasks():
    if not tasks:
        return jsonify({"error": "No tasks found"}), 404

    tasks_list = [{key: value for key, value in tasks[i].to_dict().items() if key != "details"}
                  for i in sorted(tasks.keys())]

    return jsonify(tasks_list), 200

# share with users
