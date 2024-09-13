#!/bin/sh

# Set default values for UID and GID
USER_ID=${LOCAL_USER_ID:-9001}
GROUP_ID=${LOCAL_GROUP_ID:-9001}

# Create a user and group with the same UID/GID as the host user
addgroup --gid $GROUP_ID appgroup
adduser --disabled-password --gecos '' --uid $USER_ID --gid $GROUP_ID appuser

# Change ownership of all files in /app to appuser:appgroup
chown -R appuser:appgroup /app

# Run the application as the new user
exec su -c "$@" appuser
