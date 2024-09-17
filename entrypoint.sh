#!/bin/sh

# Run database migrations
flask db upgrade

# Check if Redis should be used
if [ "$USE_REDIS" = "True" ] || [ "$USE_REDIS" = "true" ]; then
    # Start the application with Redis
    exec gunicorn -k eventlet -w 5 -b 0.0.0.0:8000 --timeout 120 app:application
else
    # Start the application without Redis
    exec gunicorn -k eventlet -w 5 -b 0.0.0.0:8000 --timeout 120 app:application
fi
