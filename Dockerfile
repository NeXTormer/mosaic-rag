FROM python:3.11-slim AS app
LABEL maintainer="Felix Holz <felix.holz@me.com>"


RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    gcc \
    git \
    python3-dev \
    libffi-dev \
    libssl-dev \
    libblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools wheel


#WORKDIR /src

#RUN git clone https://github.com/NeXTormer/mosaic-rag-frontend.git .
#
#
#RUN mkdir -p /app/frontend && mv ./build/web/* /app/frontend/


WORKDIR /app


COPY app/ ./app
COPY mosaicrs/ ./mosaicrs

COPY deepseek.apikey ./deepseek.apikey
COPY innkube.apikey ./innkube.apikey

#COPY --from=build /src/build/web ./frontend

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt



# Expose the port the app runs on
EXPOSE 5000

# Set the environment variable to disable debug mode in production
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1


# the docker host for the deployment server running redis
ENV REDIS_HOST 172.17.0.1
ENV COLOR_THEME blue-dark
ENV APP_TITLE mosaicRAG
env APP_PIPELINE_CONFIG_ALLOWED true
env APP_LOGS_ALLOWED true

# Run the app with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "300", "app.app:app"]