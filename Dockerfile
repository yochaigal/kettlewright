# Use an official Python runtime as the base image
FROM python:3.10

# Set environment variables to avoid Python buffering and enable Flask debugging
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt /app/

# Install the Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the entire application code
COPY . /app/

# Expose the port that the Flask app will run on
EXPOSE 8000

# Copy entrypoint script and set execute permissions
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Set the entrypoint to the script
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Default command
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "2", "-b", "0.0.0.0:8000", "app:application"]