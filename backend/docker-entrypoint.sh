#!/bin/sh
set -eu

mkdir -p /app/data
if [ ! -f /app/data/tracer.db ]; then
  cp /app/seed/tracer.db /app/data/tracer.db
fi

export BMSTU_DATABASE_URL="${BMSTU_DATABASE_URL:-sqlite:////app/data/tracer.db}"
python -m alembic -c /app/alembic.ini upgrade head
exec uvicorn andromeda.api.main:app --host 0.0.0.0 --port "${PORT:-8020}"
