#!/bin/sh
set -e

alembic upgrade head

if [ "${ENV}" = "production" ]; then
    exec uvicorn app.main:app --host 0.0.0.0 --port 5000
fi

exec uvicorn app.main:app --reload --host 0.0.0.0 --port 5000
