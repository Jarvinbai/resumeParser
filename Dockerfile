# Dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy only requirements file to leverage Docker cache
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY . /app

CMD uvicorn main:app --host=0.0.0.0 --reload


