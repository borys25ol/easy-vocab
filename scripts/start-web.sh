#!/bin/sh
set -e

# Migrations are not run here. Several replicas starting together would race
# on the same migration. A Kubernetes Job owns them; see k8s/migrate-job.yaml.

if [ "${ENV}" = "production" ]; then
    exec uvicorn app.main:app --host 0.0.0.0 --port 5000
fi

exec uvicorn app.main:app --reload --host 0.0.0.0 --port 5000
