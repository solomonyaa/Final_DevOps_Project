import pytest
from Task_Manager import app as flask_app
from db import db as _db


# ───────────────────────────────────────────
# Setup
# ───────────────────────────────────────────

@pytest.fixture
def app():
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    with flask_app.app_context():
        _db.create_all()
        yield flask_app
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client):
    """Register a test user and return client with auth credentials."""
    client.post('/api/users/register', json={
        "username": "testuser",
        "password": "testpass123"
    })
    return client


# base64 encoding of "testuser:testpass123"
AUTH_HEADER = {"Authorization": "Basic dGVzdHVzZXI6dGVzdHBhc3MxMjM="}


def create_sample_task(client, title="Buy groceries", details="Milk and eggs",
                       due_date="01/06/2026", category="personal", priority="medium"):
    return client.post('/api/tasks',
                       json={
                           "title": title,
                           "details": details,
                           "due_date": due_date,
                           "category": category,
                           "priority": priority
                       },
                       headers=AUTH_HEADER)


# ───────────────────────────────────────────
# Health
# ───────────────────────────────────────────

class TestHealth:
    def test_health_returns_ok(self, client):
        response = client.get('/api/health')
        assert response.status_code == 200
        assert response.get_json() == {"status": "ok"}


# ───────────────────────────────────────────
# POST /api/users/register
# ───────────────────────────────────────────

class TestRegister:
    def test_register_success(self, client):
        response = client.post('/api/users/register', json={
            "username": "newuser",
            "password": "password123"
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data['username'] == "newuser"
        assert 'password_hash' not in data

    def test_register_missing_fields(self, client):
        response = client.post('/api/users/register', json={"username": "onlyuser"})
        assert response.status_code == 400

    def test_register_duplicate_username(self, client):
        client.post('/api/users/register', json={"username": "user1", "password": "pass123"})
        response = client.post('/api/users/register', json={"username": "user1", "password": "pass123"})
        assert response.status_code == 409

    def test_register_short_password(self, client):
        response = client.post('/api/users/register', json={"username": "user1", "password": "abc"})
        assert response.status_code == 400

    def test_register_missing_json(self, client):
        response = client.post('/api/users/register')
        assert response.status_code == 415


# ───────────────────────────────────────────
# Authentication
# ───────────────────────────────────────────

class TestAuth:
    def test_no_auth_returns_401(self, auth_client):
        response = auth_client.get('/api/tasks')
        assert response.status_code == 401

    def test_wrong_password_returns_401(self, auth_client):
        response = auth_client.get('/api/tasks',
                                   headers={"Authorization": "Basic dGVzdHVzZXI6d3JvbmdwYXNz"})
        assert response.status_code == 401

    def test_valid_auth_accepted(self, auth_client):
        response = auth_client.get('/api/tasks', headers=AUTH_HEADER)
        assert response.status_code == 200


# ───────────────────────────────────────────
# POST /api/tasks
# ───────────────────────────────────────────

class TestCreateTask:
    def test_create_task_success(self, auth_client):
        response = create_sample_task(auth_client)
        assert response.status_code == 201
        data = response.get_json()
        assert data['title'] == "Buy groceries"
        assert data['category'] == "personal"
        assert data['priority'] == "medium"
        assert data['is_complete'] is False

    def test_create_task_missing_fields(self, auth_client):
        response = auth_client.post('/api/tasks',
                                    json={"title": "Only title"},
                                    headers=AUTH_HEADER)
        assert response.status_code == 400

    def test_create_task_invalid_date(self, auth_client):
        response = create_sample_task(auth_client, due_date="32/13/2026")
        assert response.status_code == 400

    def test_create_task_invalid_category(self, auth_client):
        response = create_sample_task(auth_client, category="invalid")
        assert response.status_code == 400

    def test_create_task_invalid_priority(self, auth_client):
        response = create_sample_task(auth_client, priority="invalid")
        assert response.status_code == 400

    def test_create_task_requires_auth(self, auth_client):
        response = auth_client.post('/api/tasks', json={
            "title": "Task", "details": "Details",
            "due_date": "01/06/2026", "category": "work", "priority": "high"
        })
        assert response.status_code == 401


# ───────────────────────────────────────────
# GET /api/tasks
# ───────────────────────────────────────────

class TestGetTasks:
    def test_get_all_tasks(self, auth_client):
        create_sample_task(auth_client, title="Task 1")
        create_sample_task(auth_client, title="Task 2")
        response = auth_client.get('/api/tasks', headers=AUTH_HEADER)
        assert response.status_code == 200
        assert len(response.get_json()) == 2

    def test_get_tasks_empty(self, auth_client):
        response = auth_client.get('/api/tasks', headers=AUTH_HEADER)
        assert response.status_code == 200
        assert response.get_json() == []

    def test_get_tasks_filter_by_category(self, auth_client):
        create_sample_task(auth_client, title="Personal task", category="personal")
        create_sample_task(auth_client, title="Work task", category="work")
        response = auth_client.get('/api/tasks?category=work', headers=AUTH_HEADER)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['category'] == "work"

    def test_get_tasks_filter_by_priority(self, auth_client):
        create_sample_task(auth_client, title="High task", priority="high")
        create_sample_task(auth_client, title="Low task", priority="low")
        response = auth_client.get('/api/tasks?priority=high', headers=AUTH_HEADER)
        assert response.status_code == 200
        assert len(response.get_json()) == 1

    def test_get_tasks_requires_auth(self, auth_client):
        response = auth_client.get('/api/tasks')
        assert response.status_code == 401


# ───────────────────────────────────────────
# GET /api/task/<id>
# ───────────────────────────────────────────

class TestGetTask:
    def test_get_task_success(self, auth_client):
        create_sample_task(auth_client, title="My task")
        response = auth_client.get('/api/task/1', headers=AUTH_HEADER)
        assert response.status_code == 200
        assert response.get_json()['title'] == "My task"

    def test_get_task_not_found(self, auth_client):
        response = auth_client.get('/api/task/999', headers=AUTH_HEADER)
        assert response.status_code == 404

    def test_get_task_requires_auth(self, auth_client):
        create_sample_task(auth_client)
        response = auth_client.get('/api/task/1')
        assert response.status_code == 401


# ───────────────────────────────────────────
# PATCH /api/task/<id>
# ───────────────────────────────────────────

class TestEditTask:
    def test_edit_title(self, auth_client):
        create_sample_task(auth_client)
        response = auth_client.patch('/api/task/1',
                                     json={"title": "Updated title"},
                                     headers=AUTH_HEADER)
        assert response.status_code == 200
        assert response.get_json()['task']['title'] == "Updated title"

    def test_edit_invalid_date(self, auth_client):
        create_sample_task(auth_client)
        response = auth_client.patch('/api/task/1',
                                     json={"due_date": "99/99/9999"},
                                     headers=AUTH_HEADER)
        assert response.status_code == 400

    def test_edit_invalid_category(self, auth_client):
        create_sample_task(auth_client)
        response = auth_client.patch('/api/task/1',
                                     json={"category": "invalid"},
                                     headers=AUTH_HEADER)
        assert response.status_code == 400

    def test_edit_task_not_found(self, auth_client):
        response = auth_client.patch('/api/task/999',
                                     json={"title": "Ghost"},
                                     headers=AUTH_HEADER)
        assert response.status_code == 404

    def test_edit_task_requires_auth(self, auth_client):
        create_sample_task(auth_client)
        response = auth_client.patch('/api/task/1', json={"title": "New"})
        assert response.status_code == 401


# ───────────────────────────────────────────
# DELETE /api/task/<id>
# ───────────────────────────────────────────

class TestDeleteTask:
    def test_delete_task_success(self, auth_client):
        create_sample_task(auth_client)
        response = auth_client.delete('/api/task/1', headers=AUTH_HEADER)
        assert response.status_code == 200

    def test_delete_task_no_longer_exists(self, auth_client):
        create_sample_task(auth_client)
        auth_client.delete('/api/task/1', headers=AUTH_HEADER)
        response = auth_client.get('/api/task/1', headers=AUTH_HEADER)
        assert response.status_code == 404

    def test_delete_task_not_found(self, auth_client):
        response = auth_client.delete('/api/task/999', headers=AUTH_HEADER)
        assert response.status_code == 404

    def test_delete_task_requires_auth(self, auth_client):
        create_sample_task(auth_client)
        response = auth_client.delete('/api/task/1')
        assert response.status_code == 401


# ───────────────────────────────────────────
# PATCH /api/task/<id>/complete
# ───────────────────────────────────────────

class TestSetTaskComplete:
    def test_complete_task(self, auth_client):
        create_sample_task(auth_client)
        response = auth_client.patch('/api/task/1/complete',
                                     json={"is_complete": True},
                                     headers=AUTH_HEADER)
        assert response.status_code == 200
        assert response.get_json()['task']['is_complete'] is True

    def test_uncomplete_task(self, auth_client):
        create_sample_task(auth_client)
        auth_client.patch('/api/task/1/complete',
                          json={"is_complete": True},
                          headers=AUTH_HEADER)
        response = auth_client.patch('/api/task/1/complete',
                                     json={"is_complete": False},
                                     headers=AUTH_HEADER)
        assert response.status_code == 200
        assert response.get_json()['task']['is_complete'] is False

    def test_complete_task_not_found(self, auth_client):
        response = auth_client.patch('/api/task/999/complete',
                                     json={"is_complete": True},
                                     headers=AUTH_HEADER)
        assert response.status_code == 404

    def test_complete_task_invalid_type(self, auth_client):
        create_sample_task(auth_client)
        response = auth_client.patch('/api/task/1/complete',
                                     json={"is_complete": "true"},
                                     headers=AUTH_HEADER)
        assert response.status_code == 400

    def test_complete_task_requires_auth(self, auth_client):
        create_sample_task(auth_client)
        response = auth_client.patch('/api/task/1/complete', json={"is_complete": True})
        assert response.status_code == 401
