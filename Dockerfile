# Use an official Python runtime as the base image
FROM python:3.10

# Set environment variables to avoid Python buffering and enable Flask debugging
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Set up environment variables for the UID and GID, with defaults
ARG UID=1000
ARG GID=1000

# Create a group and user with the same UID and GID as the host user
RUN groupadd --gid $GID kettlewright && \
    useradd --uid $UID --gid $GID --create-home --shell /bin/bash kettlewright

# Install the Python dependencies as root
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

# Set the correct file permissions
RUN chmod -R u+rw /app

# Switch to the non-root user before copying the application code
USER kettlewright

# Copy the application code and ensure ownership
COPY --chown=kettlewright:kettlewright . /app/

# Expose the port that the Flask app will run on
EXPOSE 8000

# Copy entrypoint script and set execute permissions
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Set the entrypoint to the script
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Default command
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "2", "-b", "0.0.0.0:8000", "app:application"]
