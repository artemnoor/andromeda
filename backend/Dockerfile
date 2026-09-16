FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./
COPY data/tracer.db /app/seed/tracer.db
COPY docker-entrypoint.sh ./

RUN pip install --no-cache-dir . \
    && chmod +x /app/docker-entrypoint.sh \
    && mkdir -p /app/data

EXPOSE 8020
ENTRYPOINT ["/app/docker-entrypoint.sh"]
