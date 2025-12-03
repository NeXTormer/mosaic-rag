
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    gcc \
    git \
    libffi-dev \
    libssl-dev \
    libblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .


RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu


FROM python:3.11-slim AS runtime
LABEL maintainer="Felix Holz <felix.holz@me.com>"

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgomp1 \
    libblas3 \
    liblapack3 \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"


COPY app/ ./app
COPY mosaicrs/ ./mosaicrs

COPY deepseek.apikey ./deepseek.apikey
COPY innkube.apikey ./innkube.apikey


EXPOSE 5000

ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV REDIS_HOST=localhost
ENV OLLAMA_HOST=localhost:11434
ENV COLOR_THEME=blue-light
ENV APP_TITLE=mosaicRAG
ENV APP_PIPELINE_CONFIG_ALLOWED=true
ENV APP_LOGS_ALLOWED=true

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "300", "app.app:app"]