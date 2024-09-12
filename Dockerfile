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

# Copy the entrypoint script and make it executable
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Set the entrypoint for the script
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Expose the port that the Flask app will run on
EXPOSE 8000

# Command to run the Flask application with Gunicorn and WebSocket support
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "2", "-b", "0.0.0.0:8000", "app:application"]
