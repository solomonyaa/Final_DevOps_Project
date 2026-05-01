# CloudTasks - Final DevOps Project

A cloud-native Task Manager application built with Python Flask, containerized with Docker, and deployed on AWS using Kubernetes and Terraform. The app includes an AI-powered assistant (OpenAI GPT-4o) that gives productivity advice on tasks.

---

## 👥 Contributors

- [solomonyaa](https://github.com/solomonyaa)
- [shayhaba](https://github.com/shayhaba)

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript |
| Database | PostgreSQL (AWS RDS) |
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
│       ├── ci.yml          # CI - runs on every PR to main
│       └── cd.yml          # CD - runs on merge to main
├── Task_Manager.py          # Flask REST API
├── Task_Module.py           # Task, Category, Priority classes
├── test_Task_Manager.py     # pytest test suite (38 tests)
├── Dockerfile               # Container definition
├── requirements.txt         # Python dependencies
├── .dockerignore            # Docker ignore rules
└── README.md
```

---

## 🚀 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/tasks` | Create a new task |
| GET | `/tasks` | Get all tasks (with optional filters) |
| GET | `/task/<id>` | Get a single task |
| PATCH | `/task/<id>` | Edit a task |
| DELETE | `/task/<id>` | Delete a task |
| PATCH | `/task/<id>/complete` | Mark task complete/incomplete |
| POST | `/task/<id>/ask` | Ask AI for advice on a task |

### Filters for `GET /tasks`

```
/tasks?category=work
/tasks?priority=high
/tasks?is_complete=false
/tasks?category=work&priority=high&is_complete=false
```

### Task fields

| Field | Type | Values |
|-------|------|--------|
| title | string | any |
| details | string | any |
| due_date | string | DD/MM/YYYY |
| category | string | personal, work, shopping |
| priority | string | low, medium, high |
| is_complete | boolean | true, false |

---

## 🐳 Running Locally with Docker

```bash
# Build the image
docker build -t cloudtasks:latest .

# Run the container
docker run -p 5000:5000 -e OPENAI_API_KEY=your-key cloudtasks:latest
```

Test it:
```bash
curl http://localhost:5000/health
```

---

## ⚙️ CI/CD Pipeline

### CI (`ci.yml`) — triggers on every Pull Request to `main`
1. Checkout code
2. Lint with flake8
3. Run 38 pytest unit tests
4. Build Docker image
5. Run container
6. Integration tests for all endpoints (GET, POST, PATCH, DELETE)
7. AI endpoint test

### CD (`cd.yml`) — triggers on merge to `main`
1. Checkout code
2. Login to Docker Hub
3. Build Docker image
4. Push to Docker Hub with two tags:
   - `latest` — always the newest version
   - `<commit-sha>` — unique tag per commit for versioning and rollback

---

## 🔐 GitHub Secrets Required

| Secret | Description |
|--------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `DOCKERHUB_USERNAME` | Docker Hub username |
| `DOCKERHUB_PASSWORD` | Docker Hub password |

---

## 📦 Docker Hub

Image: [`shayandsolomon/cloudtasks`](https://hub.docker.com/r/shayandsolomon/cloudtasks)

```bash
docker pull shayandsolomon/cloudtasks:latest
```
