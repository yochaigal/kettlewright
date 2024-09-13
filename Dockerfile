# Use an official Python runtime as the base image
FROM python:3.10

# Set environment variables to show logging
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the application
COPY . /app/

# Set ownership for the kettlewright user dynamically based on UID and GID
ARG UID=1000
ARG GID=1000
RUN groupadd -g $GID kettlewright && \
    useradd -m -u $UID -g $GID kettlewright && \
    chown -R kettlewright:kettlewright /app

# Set the user to be 'kettlewright' for running the container
USER kettlewright

# Expose the port that the Flask app will run on
EXPOSE 8000

# Command to run the Flask application with Gunicorn and WebSocket support
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "2", "-b", "0.0.0.0:8000", "app:application"]
