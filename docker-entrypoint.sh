#!/bin/bash

# Check if the UID and GID are provided
if [ -n "$UID" ] && [ -n "$GID" ]; then
    if ! getent group kettlewright >/dev/null; then
        addgroup --gid "$GID" kettlewright
    fi
    if ! id -u kettlewright >/dev/null 2>&1; then
        adduser --disabled-password --gecos '' --uid "$UID" --gid "$GID" kettlewright
    fi
fi

# Change ownership of all files in /app to the current user
chown -R kettlewright:kettlewright /app

# Execute the provided command
exec "$@"
