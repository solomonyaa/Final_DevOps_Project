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
| Database | PostgreSQL (local: Docker, production: AWS RDS) |
| Containerization | Docker, Docker Compose |
| Container Orchestration | Kubernetes (AWS EKS) |
| Infrastructure as Code | Terraform |
| Cloud | AWS (EKS, RDS, VPC, IAM, KMS, SSM) |
| CI/CD | GitHub Actions |
| Version Control | Git, GitHub |
| AI | OpenAI GPT-4o |
| Monitoring | Prometheus, Grafana |

---

## 📁 Project Structure

```
Final_DevOps_Project/
├── .github/
│   └── workflows/
│       ├── ci.yml                  # CI - runs on every PR to main
│       ├── cd.yml                  # CD - builds and pushes to Docker Hub on merge
│       ├── deploy-to-eks.yml       # Deploy - manual trigger for demo day
│       ├── terraform-apply.yml     # Manual - provisions AWS infrastructure
│       └── terraform-destroy.yml   # Manual - destroys AWS infrastructure
├── frontend/                       # React UI (Vite)
│   ├── src/
│   │   ├── pages/                  # AuthPage, Dashboard
│   │   ├── components/             # TaskCard, TaskForm, AskModal
│   │   ├── api.js                  # Axios instance
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── k8s/                            # Kubernetes manifests
│   ├── namespace.yaml              # cloudtasks namespace
│   ├── deployment.yaml             # Flask app deployment (2 replicas)
│   ├── service.yaml                # ClusterIP service
│   └── ingress.yaml                # NGINX ingress
├── terraform/                      # AWS infrastructure
│   ├── main.tf                     # VPC, EKS, RDS, KMS, bastion resources
│   ├── variables.tf                # Input variables
│   └── outputs.tf                  # Output values
├── Task_Manager.py                 # Flask REST API
├── Task_Module.py                  # Task, Category, Priority classes
├── User_Module.py                  # User model
├── db.py                           # Database init
├── test_Task_Manager.py            # pytest test suite
├── Dockerfile                      # Multi-stage build (Node + Python)
├── docker-compose.yml              # App + Postgres services
├── connect-rds.sh                  # Connect to RDS via SSM tunnel
├── requirements.txt                # Python dependencies
└── .gitignore
```

---

## 🚀 Running Locally

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
3. Build and start full Docker stack with PostgreSQL
4. Integration tests for all API endpoints
5. Verify DB state after each operation
6. Cleanup

### CD (`cd.yml`) — triggers on merge to `main`
1. Login to Docker Hub
2. Build Docker image (multi-stage: React + Python)
3. Push to Docker Hub with two tags:
   - `latest` — always the newest version
   - `<commit-sha>` — unique tag per commit for rollback

### Deploy to EKS (`deploy-to-eks.yml`) — manual trigger on demo day
1. Configure AWS credentials
2. Update kubeconfig for EKS
3. Create DockerHub pull secret
4. Create/update Kubernetes secret with DB and API credentials
5. Apply Kubernetes manifests
6. Roll out latest image to EKS deployment
7. Debug pod status on failure

### Terraform Apply (`terraform-apply.yml`) — manual trigger
1. Create S3 state bucket if not exists
2. Terraform init, validate, plan
3. Terraform apply
4. Save RDS endpoint automatically to GitHub Secrets
5. Update kubeconfig and verify EKS connection

### Terraform Destroy (`terraform-destroy.yml`) — manual trigger with confirmation
1. Requires typing `"destroy"` to confirm
2. Terraform plan destroy (preview)
3. Uninstall Helm releases (NGINX, Prometheus, Grafana)
4. Terraform destroy

---

## ☁️ AWS Infrastructure (Terraform)

All infrastructure is provisioned with Terraform and **destroyed after the demo** to avoid costs. State is stored in S3 (`cloudtasks-tfstate`) for sharing between local and CI/CD.

**Resources created:**
- VPC with public and private subnets across 2 availability zones (us-east-1b, us-east-1c)
- NAT Gateway for private subnet internet access
- EKS cluster (latest Kubernetes version) with 2 worker nodes (`t3.medium`)
- EKS cluster addons: `vpc-cni`, `coredns`, `kube-proxy`
- RDS PostgreSQL 15 (`db.t3.micro`) in private subnets — encrypted with KMS
- RDS enhanced monitoring with dedicated IAM role
- Bastion host (SSM only, no SSH) for secure RDS access
- VPC endpoints for SSM, KMS, CloudWatch Logs, and S3
- Security groups with least-privilege rules

---

## ☸️ Kubernetes

The app runs on AWS EKS with the following resources:

| Resource | Description |
|----------|-------------|
| Namespace | `cloudtasks` — isolated environment |
| Deployment | 2 Flask replicas with resource limits and readiness probe |
| Service | ClusterIP — internal load balancing |
| Ingress | NGINX — routes external traffic |

**Additional components installed via Helm:**
- NGINX Ingress Controller — external load balancer
- Prometheus + Grafana (`kube-prometheus-stack`) — monitoring

---

## 📊 Monitoring

Prometheus and Grafana are installed via the `kube-prometheus-stack` Helm chart in the `monitoring` namespace.

**Access Grafana:**
```bash
# Get external URL
kubectl get svc kube-prometheus-stack-grafana -n monitoring

# Get password
kubectl get secret -n monitoring kube-prometheus-stack-grafana \
  -o jsonpath="{.data.admin-password}" | base64 --decode
```

Default username: `admin`

---

## 🔌 Connecting to RDS

To connect to the RDS database locally via the bastion host:

```bash
./connect-rds.sh
```

Requires:
- AWS CLI configured
- SSM Session Manager plugin installed
- `psql` installed
- `.env` file with `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`

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
| `PROJECT_AWS_ADMIN_ACCESSKEY` | AWS access key ID |
| `PROJECT_AWS_ADMIN_SECRET` | AWS secret access key |
| `RDS_ENDPOINT` | RDS endpoint (set automatically by terraform-apply.yml) |
| `GH_PAT` | GitHub Personal Access Token (for updating secrets) |
| `GRAFANA_ADMIN_PASSWORD` | Grafana admin password (used by terraform-apply.yml) |

---

## 🔒 Security

- All routes require Basic Auth except `/api/health` and `/api/users/register`
- Passwords are hashed with Werkzeug `generate_password_hash`
- Usernames are always stored lowercase
- SQLAlchemy ORM prevents SQL injection
- React escapes all output preventing XSS
- Prompt injection hardened with XML delimiters and system prompt instructions
- Docker container runs as non-root user
- RDS is in a private subnet — not accessible from the internet
- RDS encrypted at rest with AWS KMS
- RDS security group only allows connections from EKS nodes and bastion
- Bastion host accessible via SSM only — no open ports, no SSH keys
- VPC endpoints for SSM, KMS, CloudWatch, S3 — no internet exposure

---

## 📦 Docker Hub

Image: [`shayandsolomon/cloudtasks`](https://hub.docker.com/r/shayandsolomon/cloudtasks)

```bash
docker pull shayandsolomon/cloudtasks:latest
```
