#!/bin/sh

# Run database migrations
flask db upgrade

# Set the number of workers (default to 1 if not set)
WORKERS=${WORKERS:-1}

# Check if Redis should be used
if [ "$USE_REDIS" = "True" ] || [ "$USE_REDIS" = "true" ]; then
    # Start the application with Redis and the specified number of workers
    exec gunicorn -k eventlet -w $WORKERS -b 0.0.0.0:8000 --timeout 120 app:application
else
    # Start the application without Redis and the specified number of workers
    exec gunicorn -k eventlet -w $WORKERS -b 0.0.0.0:8000 --timeout 120 app:application
fi
