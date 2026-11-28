#!/bin/bash
# Deploys a stage image on the EC2 host; if it fails after changing, rolls back to the
# last stable version. Runs through SSM Run Command.
# Required env: ECR_IMAGE (registry/repository), IMAGE_TAG, AWS_REGION, S3_PREFIX.
# Optional env: STABLE_TAG, the last stable version (empty: nothing to roll back to).
# Its last line says how it ended: "Deploy result: ...".
set -euo pipefail

: "${ECR_IMAGE:?ECR_IMAGE is required}"
: "${IMAGE_TAG:?IMAGE_TAG is required}"
: "${AWS_REGION:?AWS_REGION is required}"
: "${S3_PREFIX:?S3_PREFIX is required}"
STABLE_TAG=${STABLE_TAG:-}
no_rollback_reason='There is no stable version to roll back to'

PARAMETERS_PATH='/peru-town-hub/stage/'
HEALTH_URL='http://localhost/api/v1/health/'
COMPOSE_NAME='docker-compose.stage.yml'
# The compose of what runs (for work by hand), of the new version and of the stable one.
RUNNING_COMPOSE=$COMPOSE_NAME
NEW_COMPOSE='docker-compose.new.yml'
STABLE_COMPOSE='docker-compose.stable.yml'
ENV_BACKUP='.env.previous'
IRREVERSIBLE_EXIT_CODE=3 # migration_state restore: a migration cannot go back

cd "$(dirname "$0")"
export ECR_IMAGE AWS_REGION

# Both share the project (this folder), so either one replaces the other's web.
new() { IMAGE_TAG=$IMAGE_TAG docker compose -f "$NEW_COMPOSE" "$@"; }
stable() { IMAGE_TAG=$STABLE_TAG docker compose -f "$STABLE_COMPOSE" "$@"; }

# The new version knows every migration, the stable one may not.
migration_state() {
    new run --rm -T web python manage.py migration_state "$@"
}

result() {
    echo "Deploy result: $*"
}

no_rollback() {
    echo "::warning::$1: a failure will need a fix forward." >&2
    no_rollback_reason=$1
    STABLE_TAG=''
}

write_env() {
    echo "Writing .env from Parameter Store ($PARAMETERS_PATH)"
    if [ -f .env ]; then cp -p .env "$ENV_BACKUP"; fi
    aws ssm get-parameters-by-path \
        --region "$AWS_REGION" \
        --path "$PARAMETERS_PATH" \
        --with-decryption \
        --query 'Parameters[*].[Name,Value]' \
        --output text \
        | while IFS=$'\t' read -r name value; do
            # Docker Compose interpolates "$" in env files, so escape it as "$$".
            printf '%s=%s\n' "${name##*/}" "${value//\$/\$\$}"
        done > .env
    chmod 600 .env
}

download_composes() {
    echo "Downloading the compose of $IMAGE_TAG"
    aws s3 cp --only-show-errors "$S3_PREFIX/$IMAGE_TAG/$COMPOSE_NAME" "$NEW_COMPOSE"
    if [ -n "$STABLE_TAG" ] && ! aws s3 cp --only-show-errors \
        "$S3_PREFIX/$STABLE_TAG/$COMPOSE_NAME" "$STABLE_COMPOSE"; then
        no_rollback "The compose of the stable version $STABLE_TAG is not in S3"
    fi
}

pull_images() {
    echo "Pulling $IMAGE_TAG"
    aws ecr get-login-password --region "$AWS_REGION" \
        | docker login --username AWS --password-stdin "${ECR_IMAGE%%/*}"
    new pull --quiet
    if [ -n "$STABLE_TAG" ] && ! stable pull --quiet web; then
        no_rollback "The stable version $STABLE_TAG could not be pulled"
    fi
}

# Phase 1: nothing that runs changes. The settings load with the new .env, or the
# check names what is missing (never its value).
verify() {
    write_env
    download_composes
    pull_images
    echo 'Checking the settings with the new .env'
    new run --rm --no-deps -T --entrypoint python web \
        manage.py check --deploy --fail-level WARNING
    new up -d --wait db
    echo 'Recording the migration state'
    recorded_state=$(migration_state record)
    echo "$recorded_state"
}

stop_without_changes() {
    if [ -f "$ENV_BACKUP" ]; then mv "$ENV_BACKUP" .env; else rm -f .env; fi
    result "Stopped without changes: the verification failed (see above)." \
        "Stage keeps running its current version."
}

# Phase 2: migrate and start the new version.
change() {
    rm -f "$ENV_BACKUP"
    cp "$NEW_COMPOSE" "$RUNNING_COMPOSE"
    echo "Deploying $ECR_IMAGE:$IMAGE_TAG"
    new run --rm web python manage.py migrate --noinput
    new run --rm web python manage.py createcachetable
    new up -d --remove-orphans
}

healthy() {
    echo "Checking $HEALTH_URL"
    for attempt in $(seq 1 10); do
        if curl --fail --silent --show-error "$HEALTH_URL"; then
            echo
            return 0
        fi
        echo "Health check attempt $attempt failed, retrying..."
        sleep 3
    done
    return 1
}

what_is_left() {
    local image state
    image=$(docker inspect --format '{{.Config.Image}}' "$(new ps -q web)" \
        2>/dev/null || echo 'none')
    state=$(migration_state record 2>/dev/null || echo 'unknown')
    echo "Left: web runs $image; migration state: $state."
}

# Phase 3: the migrations back to the recorded state, then the stable version.
roll_back() {
    local reverted code
    echo "Rolling back to $STABLE_TAG"
    if reverted=$(migration_state restore "$recorded_state"); then
        echo "$reverted"
    else
        code=$?
        if [ "$code" -eq "$IRREVERSIBLE_EXIT_CODE" ]; then
            result "Fix forward: a migration cannot be reversed. $(what_is_left)"
        else
            result "Rollback failed: the migrations did not go back." \
                "$(what_is_left) Finish it by hand (deploy runbook)."
        fi
        return
    fi
    cp "$STABLE_COMPOSE" "$RUNNING_COMPOSE"
    if stable up -d --remove-orphans web && healthy; then
        result "Rolled back to $STABLE_TAG; ${reverted//$'\n'/; }."
    else
        result "Rollback failed: $STABLE_TAG did not start." \
            "$(what_is_left) Finish it by hand (deploy runbook)."
    fi
}

after_change_failure() {
    echo "Deploy of $IMAGE_TAG failed" >&2
    new logs --tail 50 web >&2 || true
    if [ -z "$STABLE_TAG" ]; then
        result "Fix forward: $no_rollback_reason. $(what_is_left)"
    else
        roll_back
    fi
}

# Runs once, in this shell only (subshells do not inherit an EXIT trap).
on_exit() {
    local code=$?
    trap - EXIT
    if [ "$code" -eq 0 ]; then return; fi
    set +e
    case $phase in
        verify) stop_without_changes ;;
        change) after_change_failure ;;
    esac
    exit 1
}

phase=verify
trap on_exit EXIT
verify
phase=change
change
if ! healthy; then exit 1; fi
phase=succeeded
docker image prune --force
result "Succeeded: $IMAGE_TAG is running."
