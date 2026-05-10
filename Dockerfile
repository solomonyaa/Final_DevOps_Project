# Stage 1: Build React frontend
FROM node:18-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

# Stage 2: Python backend + React static files
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY db.py Task_Module.py User_Module.py Task_Manager.py ./
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist
RUN useradd -m appuser && chown -R appuser /app
USER appuser
EXPOSE 5000
CMD ["python", "Task_Manager.py"]
