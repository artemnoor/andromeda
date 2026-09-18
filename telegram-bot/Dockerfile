FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY telegram-bot/pyproject.toml telegram-bot/pyproject.toml
COPY telegram-bot/src telegram-bot/src
RUN pip install --no-cache-dir ./telegram-bot \
    && useradd --system --uid 10001 --home-dir /var/lib/andromeda-telegram andromeda \
    && mkdir -p /var/lib/andromeda-telegram \
    && chown -R andromeda:andromeda /var/lib/andromeda-telegram

USER andromeda
ENTRYPOINT ["andromeda-telegram"]
