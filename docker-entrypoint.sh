#!/bin/bash

# Check if the UID and GID are provided
if [ -n "$UID" ] && [ -n "$GID" ]; then
  # Create a group and user with the provided UID and GID
  if ! getent group kettlewright >/dev/null; then
    groupadd --gid $GID kettlewright
  fi
  if ! id -u kettlewright >/dev/null 2>&1; then
    useradd --uid $UID --gid $GID --create-home --shell /bin/bash kettlewright
  fi

  # Change ownership of the app directory to the new user
  chown -R kettlewright:kettlewright /app
fi

# Run the provided command
exec "$@"
