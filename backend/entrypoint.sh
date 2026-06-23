#!/bin/bash
set -e

# Wait for DB
until PGPASSWORD=password psql -h db -U tracker -d token_tracker -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - running init script"
python scripts/init_db.py

>&2 echo "Starting backend"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
