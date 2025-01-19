FROM python:3.11-slim AS app
LABEL maintainer="Felix Holz <felix.holz@tugraz.at>"

# Set the working directory in the container
WORKDIR /app

# Install system dependencies and Python dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt to the working directory
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app and mosaicrs folders into the container
COPY app/ ./app
COPY mosaicrs/ ./mosaicrs

COPY deepseek.apikey ./deepseek.apikey

# Expose the port the app runs on
EXPOSE 5000

# Set the environment variable to disable debug mode in production
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Run the app with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "300", "app.app:app"]