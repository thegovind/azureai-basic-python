# syntax=docker/dockerfile:1

FROM python:3.11-slim

WORKDIR /code

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PORT=80
ENV PYTHONPATH=/code
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=api.main
ENV FLASK_ENV=production
ENV GUNICORN_CMD_ARGS="--log-level debug --access-logfile - --error-logfile - --capture-output"

# Create a non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /code
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# Command to run the application
ENTRYPOINT ["gunicorn"]
CMD ["--bind", "0.0.0.0:80", \
     "--workers", "1", \
     "--threads", "8", \
     "--timeout", "120", \
     "--keep-alive", "2", \
     "--log-level", "debug", \
     "--error-logfile", "-", \
     "--access-logfile", "-", \
     "--capture-output", \
     "api.main:app"]
