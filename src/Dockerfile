# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /code

# Install any needed system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first so we can cache pip installs
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (including prompt.prompty, __init__.py, etc.)
COPY . .

# Set environment variables
ENV PORT=8000
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/code
ENV RUNNING_IN_PRODUCTION=true

# Expose port 8000 for container platforms
EXPOSE 8000

# Use uvicorn, calling your factory function
CMD ["uvicorn", "api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
