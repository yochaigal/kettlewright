# Use an official Python runtime as the base image
FROM python:3.10

# Set environment variables to avoid Python buffering and enable Flask debugging
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Set up environment variables for the UID and GID
ARG UID=1000
ARG GID=1000

# Create a user with the same UID and GID as the host user
RUN addgroup --gid $GID kettlewright && \
    adduser --disabled-password --gecos '' --uid $UID --gid $GID kettlewright

# Change ownership of the entire app directory to the current user
RUN chown -R kettlewright:kettlewright /app

# Switch to the newly created user before copying files
USER kettlewright

# Copy the requirements file to the container
COPY requirements.txt /app/

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code into the container
COPY . /app/

# Expose the port that the Flask app will run on
EXPOSE 5000

# Command to run the Flask application with Gunicorn and WebSocket support
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "2", "-b", "0.0.0.0:5000", "app:application"]
