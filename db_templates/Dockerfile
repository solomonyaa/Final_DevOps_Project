FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY db.py .
COPY Task_Module.py .
COPY User_Module.py .
COPY Task_Manager.py .

EXPOSE 5000

CMD ["python", "Task_Manager.py"]
