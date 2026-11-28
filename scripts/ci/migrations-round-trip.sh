#!/bin/bash
# Every migration goes forward, back to zero and forward again, with the command the
# deploy rolls back with. Runs on a throwaway database, never the development one.
set -euo pipefail

DATABASE='migrations_round_trip'

cd "$(dirname "$0")/../.."

web() {
    docker compose run --rm -T -e POSTGRES_DB="$DATABASE" web "$@"
}

# Runs in the db container, where POSTGRES_USER is set.
db() {
    docker compose exec -T db sh -c "$1 -U \"\$POSTGRES_USER\" $DATABASE"
}

docker compose up -d --wait db
db 'dropdb --if-exists'
db createdb

empty_state=$(web python manage.py migration_state record)
echo "Forward: every migration"
web python manage.py migrate --noinput
echo "Back: every migration to zero"
web python manage.py migration_state restore "$empty_state"
echo "Forward again"
web python manage.py migrate --noinput

db dropdb
