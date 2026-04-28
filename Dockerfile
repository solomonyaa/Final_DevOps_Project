# ───────────────────────────────────────────
# Stage 1: Base image
# ───────────────────────────────────────────
FROM python:3.11-slim

# ───────────────────────────────────────────
# Stage 2: Set working directory
# ───────────────────────────────────────────
WORKDIR /app

# ───────────────────────────────────────────
# Stage 3: Install dependencies
# ───────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ───────────────────────────────────────────
# Stage 4: Copy application code
# ───────────────────────────────────────────
COPY Task_Module.py .
COPY Task_Manager.py .

# ───────────────────────────────────────────
# Stage 5: Expose port and run
# ───────────────────────────────────────────
EXPOSE 5000

CMD ["python", "Task_Manager.py"]
