#!/bin/bash

# Check if the UID and GID are provided
if [ -n "$UID" ] && [ -n "$GID" ]; then
    # Check if the user with UID already exists
    if ! id -u kettlewright >/dev/null 2>&1; then
        # Create group if it does not exist
        if ! getent group kettlewright >/dev/null; then
            addgroup --gid "$GID" kettlewright
        fi

        # Create user if it does not exist
        adduser --disabled-password --gecos '' --uid "$UID" --gid "$GID" kettlewright
    else
        echo "User with UID $UID already exists, skipping user and group creation"
    fi
fi

# Ensure the instance folder exists
if [ ! -d "/app/instance" ]; then
    mkdir /app/instance
fi

# Run database migrations without using sudo (kettlewright user is already active)
echo "Running database migrations..."
flask db upgrade

# Execute the provided command (e.g., starting the Flask application)
exec "$@"
