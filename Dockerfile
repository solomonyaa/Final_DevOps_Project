# Start by pulling the python image
FROM python:3.12-alpine

# Switch working directory
WORKDIR /app

# Copy the requirements file into the image
COPY ./requirements.txt requirements.txt

# Copy all application files
COPY ./Scheduler_API.py Scheduler_API.py
COPY ./Meeting_Module.py Meeting_Module.py

# Create virtual environment
RUN python -m venv venv
ENV PATH=/app/venv/bin:$PATH

# Install the dependencies and packages in the requirements file
RUN pip install -r requirements.txt

# Expose the port Flask runs on
EXPOSE 5000

# Configure the container to run in an executed manner
ENTRYPOINT ["python"]

CMD ["Scheduler_API.py"]
