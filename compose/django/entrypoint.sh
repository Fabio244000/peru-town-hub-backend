#!/bin/bash
set -e

echo 'Waiting for Postgres...'
while ! pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" > /dev/null 2>&1; do
    sleep 1
done
echo 'Postgres ready.'

exec "$@"
