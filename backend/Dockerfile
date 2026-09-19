FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY alembic ./alembic
COPY scripts ./scripts
COPY alembic.ini ./
COPY docker-entrypoint.sh ./

RUN apt-get update \
    && apt-get install --no-install-recommends -y poppler-utils \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv==0.11.28 \
    && uv sync --frozen --no-dev \
    && chmod +x /app/docker-entrypoint.sh

ENV PATH="/app/.venv/bin:${PATH}"

EXPOSE 8020
ENTRYPOINT ["/app/docker-entrypoint.sh"]
