#!/bin/bash
set -e

# Messages go to stderr: stdout is the command's output (the deploy reads it).
echo 'Waiting for Postgres...' >&2
while ! pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" > /dev/null 2>&1; do
    sleep 1
done
echo 'Postgres ready.' >&2

exec "$@"
