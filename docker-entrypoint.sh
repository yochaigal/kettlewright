#!/bin/bash

# Check if the UID and GID are provided (these should be passed in when running the container)
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

    # Change ownership of all files in /app to the created user and group
    chown -R "$UID":"$GID" /app
else
    echo "UID and GID must be provided"
    exit 1
fi

# Ensure the instance folder has the correct ownership
chown -R "$UID":"$GID" /app/instance

# Run database migrations
echo "Running database migrations..."
flask db upgrade

# Execute the provided command (e.g., starting the Flask application with Gunicorn)
exec "$@"
