FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Startup: migrations (idempotente) + seed (idempotente) + servidor
# docker-compose.yml sobrescreve esse CMD com --reload para dev local
CMD ["sh", "-c", "alembic upgrade head && python -m app.seeds.initial && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
