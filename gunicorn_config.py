workers = 2  # Reduce the number of workers
worker_class = 'gevent'  # Use async workers
worker_connections = 1000
timeout = 60
max_requests = 1000
max_requests_jitter = 50