#!/bin/bash
set -e

# Wait for DB
until pg_isready -h db -U tracker -d token_tracker; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - running init script"
export PYTHONPATH=$PYTHONPATH:.
python scripts/init_db.py

>&2 echo "Starting backend"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
