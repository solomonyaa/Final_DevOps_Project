import pytest
from Task_Manager import app, tasks
from Task_Module import Task


# ───────────────────────────────────────────
# Setup
# ───────────────────────────────────────────

@pytest.fixture(autouse=True)
def clear_tasks():
    """Clear tasks dict and reset static_id before every test."""
    tasks.clear()
    Task.static_id = 1
    yield
    tasks.clear()
    Task.static_id = 1


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def create_sample_task(client, title="Buy groceries", details="Milk and eggs",
                       due_date="01/06/2026", category="personal", priority="medium"):
    """Helper to create a task and return the response."""
    return client.post('/tasks', json={
        "title": title,
        "details": details,
        "due_date": due_date,
        "category": category,
        "priority": priority
    })


# ───────────────────────────────────────────
# Health
# ───────────────────────────────────────────

class TestHealth:
    def test_health_returns_ok(self, client):
        response = client.get('/health')
        assert response.status_code == 200
        assert response.get_json() == {"status": "ok"}


# ───────────────────────────────────────────
# POST /tasks
# ───────────────────────────────────────────

class TestCreateTask:
    def test_create_task_success(self, client):
        response = create_sample_task(client)
        assert response.status_code == 201
        data = response.get_json()
        assert data['title'] == "Buy groceries"
        assert data['details'] == "Milk and eggs"
        assert data['due_date'] == "01/06/2026"
        assert data['category'] == "personal"
        assert data['priority'] == "medium"
        assert data['is_complete'] == False
        assert data['id'] == 1

    def test_create_task_missing_fields(self, client):
        response = client.post('/tasks', json={"title": "Only title"})
        assert response.status_code == 400
        data = response.get_json()
        assert "Missing required fields" in data['error']

    def test_create_task_invalid_date(self, client):
        response = create_sample_task(client, due_date="32/13/2026")
        assert response.status_code == 400

    def test_create_task_invalid_category(self, client):
        response = create_sample_task(client, category="invalid")
        assert response.status_code == 400

    def test_create_task_invalid_priority(self, client):
        response = create_sample_task(client, priority="invalid")
        assert response.status_code == 400

    def test_create_task_missing_json(self, client):
        response = client.post('/tasks')
        assert response.status_code == 415

    def test_create_multiple_tasks_increments_id(self, client):
        r1 = create_sample_task(client, title="Task 1")
        r2 = create_sample_task(client, title="Task 2")
        assert r1.get_json()['id'] == 1
        assert r2.get_json()['id'] == 2


# ───────────────────────────────────────────
# GET /tasks
# ───────────────────────────────────────────

class TestGetTasks:
    def test_get_all_tasks(self, client):
        create_sample_task(client, title="Task 1")
        create_sample_task(client, title="Task 2")
        response = client.get('/tasks')
        assert response.status_code == 200
        assert len(response.get_json()) == 2

    def test_get_tasks_empty(self, client):
        response = client.get('/tasks')
        assert response.status_code == 404

    def test_get_tasks_filter_by_category(self, client):
        create_sample_task(client, title="Personal task", category="personal")
        create_sample_task(client, title="Work task", category="work")
        response = client.get('/tasks?category=work')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['category'] == "work"

    def test_get_tasks_filter_by_priority(self, client):
        create_sample_task(client, title="High task", priority="high")
        create_sample_task(client, title="Low task", priority="low")
        response = client.get('/tasks?priority=high')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['priority'] == "high"

    def test_get_tasks_filter_by_is_complete(self, client):
        create_sample_task(client, title="Task 1")
        create_sample_task(client, title="Task 2")
        client.patch('/task/1/complete', json={"is_complete": True})
        response = client.get('/tasks?is_complete=false')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['is_complete'] == False

    def test_get_tasks_combined_filters(self, client):
        create_sample_task(client, title="Work high", category="work", priority="high")
        create_sample_task(client, title="Work low", category="work", priority="low")
        create_sample_task(client, title="Personal high", category="personal", priority="high")
        response = client.get('/tasks?category=work&priority=high')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['title'] == "Work high"

    def test_get_tasks_sorted_by_due_date(self, client):
        create_sample_task(client, title="Later task", due_date="10/06/2026")
        create_sample_task(client, title="Earlier task", due_date="01/06/2026")
        response = client.get('/tasks')
        data = response.get_json()
        assert data[0]['title'] == "Earlier task"
        assert data[1]['title'] == "Later task"


# ───────────────────────────────────────────
# GET /task/<id>
# ───────────────────────────────────────────

class TestGetTask:
    def test_get_task_success(self, client):
        create_sample_task(client, title="My task")
        response = client.get('/task/1')
        assert response.status_code == 200
        assert response.get_json()['title'] == "My task"

    def test_get_task_includes_details(self, client):
        create_sample_task(client, details="Important details")
        response = client.get('/task/1')
        assert response.get_json()['details'] == "Important details"

    def test_get_task_not_found(self, client):
        response = client.get('/task/999')
        assert response.status_code == 404

    def test_get_task_invalid_id(self, client):
        response = client.get('/task/abc')
        assert response.status_code == 404


# ───────────────────────────────────────────
# PATCH /task/<id>
# ───────────────────────────────────────────

class TestEditTask:
    def test_edit_title(self, client):
        create_sample_task(client)
        response = client.patch('/task/1', json={"title": "Updated title"})
        assert response.status_code == 200
        assert response.get_json()['task']['title'] == "Updated title"

    def test_edit_due_date(self, client):
        create_sample_task(client)
        response = client.patch('/task/1', json={"due_date": "15/07/2026"})
        assert response.status_code == 200
        assert response.get_json()['task']['due_date'] == "15/07/2026"

    def test_edit_category(self, client):
        create_sample_task(client)
        response = client.patch('/task/1', json={"category": "work"})
        assert response.status_code == 200
        assert response.get_json()['task']['category'] == "work"

    def test_edit_priority(self, client):
        create_sample_task(client)
        response = client.patch('/task/1', json={"priority": "high"})
        assert response.status_code == 200
        assert response.get_json()['task']['priority'] == "high"

    def test_edit_multiple_fields(self, client):
        create_sample_task(client)
        response = client.patch('/task/1', json={"title": "New title", "priority": "low"})
        assert response.status_code == 200
        data = response.get_json()['task']
        assert data['title'] == "New title"
        assert data['priority'] == "low"

    def test_edit_invalid_date(self, client):
        create_sample_task(client)
        response = client.patch('/task/1', json={"due_date": "99/99/9999"})
        assert response.status_code == 400

    def test_edit_invalid_category(self, client):
        create_sample_task(client)
        response = client.patch('/task/1', json={"category": "invalid"})
        assert response.status_code == 400

    def test_edit_invalid_priority(self, client):
        create_sample_task(client)
        response = client.patch('/task/1', json={"priority": "invalid"})
        assert response.status_code == 400

    def test_edit_task_not_found(self, client):
        response = client.patch('/task/999', json={"title": "Ghost"})
        assert response.status_code == 404

    def test_edit_task_missing_json(self, client):
        create_sample_task(client)
        response = client.patch('/task/1')
        assert response.status_code == 415


# ───────────────────────────────────────────
# DELETE /task/<id>
# ───────────────────────────────────────────

class TestDeleteTask:
    def test_delete_task_success(self, client):
        create_sample_task(client)
        response = client.delete('/task/1')
        assert response.status_code == 200
        assert response.get_json() == {"success": True}

    def test_delete_task_no_longer_exists(self, client):
        create_sample_task(client)
        client.delete('/task/1')
        response = client.get('/task/1')
        assert response.status_code == 404

    def test_delete_task_not_found(self, client):
        response = client.delete('/task/999')
        assert response.status_code == 404


# ───────────────────────────────────────────
# PATCH /task/<id>/complete
# ───────────────────────────────────────────

class TestSetTaskComplete:
    def test_complete_task(self, client):
        create_sample_task(client)
        response = client.patch('/task/1/complete', json={"is_complete": True})
        assert response.status_code == 200
        assert response.get_json()['task']['is_complete'] == True

    def test_uncomplete_task(self, client):
        create_sample_task(client)
        client.patch('/task/1/complete', json={"is_complete": True})
        response = client.patch('/task/1/complete', json={"is_complete": False})
        assert response.status_code == 200
        assert response.get_json()['task']['is_complete'] == False

    def test_complete_task_not_found(self, client):
        response = client.patch('/task/999/complete', json={"is_complete": True})
        assert response.status_code == 404

    def test_complete_task_missing_field(self, client):
        create_sample_task(client)
        response = client.patch('/task/1/complete', json={})
        assert response.status_code == 400

    def test_complete_task_invalid_type(self, client):
        create_sample_task(client)
        response = client.patch('/task/1/complete', json={"is_complete": "true"})
        assert response.status_code == 400

    def test_complete_task_missing_json(self, client):
        create_sample_task(client)
        response = client.patch('/task/1/complete')
        assert response.status_code == 415
