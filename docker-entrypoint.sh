#!/bin/bash

# Create the user and group if they do not exist, using the provided UID and GID
if [ -n "$UID" ] && [ -n "$GID" ]; then
    if ! getent group kettlewright >/dev/null; then
        addgroup --gid "$GID" kettlewright
    fi
    if ! id -u kettlewright >/dev/null 2>&1; then
        adduser --disabled-password --gecos '' --uid "$UID" --gid "$GID" kettlewright
    fi

    # Set ownership of the /app directory
    chown -R kettlewright:kettlewright /app
fi

# Execute the original command
exec "$@"
