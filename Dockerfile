# Use an official Python runtime as the base image
FROM python:3.10

# Set environment variables to show logging
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest of the application code
COPY . /app/

# Copy the entrypoint script and make it executable
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Add the ARG instructions to allow UID and GID to be passed during build
ARG UID=1000
ARG GID=1000

# Create a group and user inside the container with the same UID and GID
RUN groupadd -g $GID kettlewright && \
    useradd -u $UID -g $GID -m kettlewright && \
    chown -R kettlewright:kettlewright /app

# Ensure the default user inside the container is kettlewright
USER kettlewright

# Expose the port that the Flask app will run on
EXPOSE 8000

# Set the entrypoint to use your entrypoint script
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Command to run the Flask application with Gunicorn and WebSocket support
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "2", "-b", "0.0.0.0:8000", "app:application"]
