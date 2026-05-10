# CloudTasks - Final DevOps Project

A cloud-native Task Manager application built with Python Flask and React, containerized with Docker, and deployed on AWS using Kubernetes and Terraform. The app includes an AI-powered assistant (OpenAI GPT-4o) that gives productivity advice on tasks.

---

## 👥 Contributors

- [solomonyaa](https://github.com/solomonyaa)
- [shayhaba](https://github.com/shayhaba)

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask |
| Frontend | React, Vite |
| Database | PostgreSQL |
| Containerization | Docker |
| Container Orchestration | Kubernetes (AWS EKS) |
| Infrastructure as Code | Terraform |
| Cloud | AWS (EKS, RDS, VPC, IAM) |
| CI/CD | GitHub Actions |
| Version Control | Git, GitHub |
| AI | OpenAI GPT-4o |

---

## 📁 Project Structure

```
Final_DevOps_Project/
├── .github/
│   └── workflows/
│       ├── ci.yml              # CI - runs on every PR to main
│       └── cd.yml              # CD - runs on merge to main
├── frontend/                   # React UI (Vite)
│   ├── src/
│   │   ├── pages/              # AuthPage, Dashboard
│   │   ├── components/         # TaskCard, TaskForm, AskModal
│   │   ├── api.js              # Axios instance
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── Task_Manager.py             # Flask REST API
├── Task_Module.py              # Task, Category, Priority classes
├── User_Module.py              # User model
├── db.py                       # Database init
├── test_Task_Manager.py        # pytest test suite
├── Dockerfile                  # Multi-stage build (Node + Python)
├── docker-compose.yml          # App + Postgres services
├── requirements.txt            # Python dependencies
└── .gitignore
```

---

## 🚀 Running the App

The only requirement is **Docker**.

```bash
# Set environment variables
export POSTGRES_USER=your_user
export POSTGRES_PASSWORD=your_password
export POSTGRES_DB=taskdb
export OPENAI_API_KEY=your_openai_key

# Start everything
docker compose up
```

Open your browser at **http://localhost:5000**

To stop:
```bash
docker compose down
```

---

## 🌐 API Endpoints

All endpoints are prefixed with `/api`.

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/health` | No | Health check |
| POST | `/api/users/register` | No | Register a new user |
| POST | `/api/tasks` | Yes | Create a new task |
| GET | `/api/tasks` | Yes | Get all tasks (with optional filters) |
| GET | `/api/task/<id>` | Yes | Get a single task |
| PATCH | `/api/task/<id>` | Yes | Edit a task |
| DELETE | `/api/task/<id>` | Yes | Delete a task |
| PATCH | `/api/task/<id>/complete` | Yes | Mark task complete/incomplete |
| POST | `/api/task/<id>/ask` | Yes | Ask AI for advice on a task |

### Filters for `GET /api/tasks`

```
/api/tasks?category=work
/api/tasks?priority=high
/api/tasks?is_complete=false
/api/tasks?category=work&priority=high&is_complete=false
```

### Task fields

| Field | Type | Values |
|-------|------|--------|
| title | string | max 30 chars |
| details | string | max 500 chars |
| due_date | string | DD/MM/YYYY |
| category | string | personal, work, shopping |
| priority | string | low, medium, high |
| is_complete | boolean | true, false |

---

## ⚙️ CI/CD Pipeline

### CI (`ci.yml`) — triggers on every Pull Request to `main`
1. Lint with flake8
2. Run pytest unit tests (SQLite in memory)
3. Build and start full Docker stack
4. Integration tests for all API endpoints
5. Verify DB state after each operation
6. Cleanup

### CD (`cd.yml`) — triggers on merge to `main`
1. Login to Docker Hub
2. Build Docker image (multi-stage: React + Python)
3. Push to Docker Hub with two tags:
   - `latest` — always the newest version
   - `<commit-sha>` — unique tag per commit for rollback

---

## 🔐 GitHub Secrets Required

| Secret | Description |
|--------|-------------|
| `DOCKERHUB_USERNAME` | Docker Hub username |
| `DOCKERHUB_PASSWORD` | Docker Hub access token |
| `POSTGRES_USER` | PostgreSQL username |
| `POSTGRES_PASSWORD` | PostgreSQL password |
| `POSTGRES_DB` | PostgreSQL database name |
| `OPENAI_API_KEY` | OpenAI API key |

---

## 🔒 Security

- All routes require Basic Auth except `/api/health` and `/api/users/register`
- Passwords are hashed with Werkzeug `generate_password_hash`
- Usernames are always stored lowercase
- SQLAlchemy ORM prevents SQL injection
- React escapes all output preventing XSS
- Prompt injection hardened with XML delimiters and system prompt instructions
- Docker container runs as non-root user

---

## 📦 Docker Hub

Image: [`shayandsolomon/cloudtasks`](https://hub.docker.com/r/shayandsolomon/cloudtasks)

```bash
docker pull shayandsolomon/cloudtasks:latest
```
