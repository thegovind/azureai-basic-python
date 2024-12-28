import multiprocessing
import os

# Basic configuration
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
worker_class = "uvicorn.workers.UvicornWorker"
workers = 2  # Start with 2 workers for Container Apps
threads = 4

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Timeouts
timeout = 120
keepalive = 5

# Reload in development only
reload = not os.getenv("RUNNING_IN_PRODUCTION", False)

# Production settings
max_requests = 1000
max_requests_jitter = 50
graceful_timeout = 30
