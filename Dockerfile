# Use an official Python runtime as the base image
FROM python:3.10

# Set environment variables to avoid Python buffering and enable Flask debugging
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

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
