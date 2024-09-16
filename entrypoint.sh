#!/bin/sh

# Run database migrations
flask db upgrade

# Start the application
exec gunicorn -k eventlet -w 2 -b 0.0.0.0:8000 app:application