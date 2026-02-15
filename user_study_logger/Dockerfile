# Use a lightweight Python base image
FROM python:3.9-slim

# Set working directory inside the container
WORKDIR /app

# Install system dependencies (none needed for basic sqlite/flask)
# Install Python dependencies
RUN pip install --no-cache-dir flask flask-cors

# Copy the server script into the container
COPY server.py .

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
CMD ["python", "server.py"]