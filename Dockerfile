# syntax=docker/dockerfile:1

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.title="MHDDoS" \
      org.opencontainers.image.description="Layer 4/7 stress-testing toolkit" \
      org.opencontainers.image.source="https://github.com/MatrixTM/MHDDoS" \
      org.opencontainers.image.licenses="MIT" \
      maintainer="0xkatana"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
# git is needed only to resolve the PyRoxy git dependency. Install git, install
# the Python dependencies, then purge git in the same layer so it never reaches
# the final image.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove git \
    && rm -rf /var/lib/apt/lists/*

COPY start.py config.json ./
COPY files ./files

STOPSIGNAL SIGINT

ENTRYPOINT ["python", "start.py"]
