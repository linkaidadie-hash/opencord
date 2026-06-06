FROM python:3.12-slim

# Build context 是项目根，所以路径是相对根
WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY apps/api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Code: api + packages（packages/ai 也要进来）
COPY apps/api ./apps/api
COPY packages ./packages

# Python path 让 apps/api 能 import packages.ai
ENV PYTHONPATH=/app:/app/apps/api
WORKDIR /app/apps/api

# Upload dir
RUN mkdir -p /app/uploads

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
