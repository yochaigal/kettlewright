#!/bin/sh

# Run database migrations
flask db upgrade

# Set the number of workers (default to 1 if not set)
WORKERS=${WORKERS:-1}

if [ "$USE_REDIS" = "True" ] || [ "$USE_REDIS" = "true" ]; then
    exec gunicorn -k gevent --preload -w $WORKERS -b 0.0.0.0:8000 --timeout 120 wsgi:application
else
    exec gunicorn -k gevent --preload -w $WORKERS -b 0.0.0.0:8000 --timeout 120 wsgi:application
fi
