#!/bin/bash
# Deploys a stage image on the EC2 host. Runs through SSM Run Command.
# Required env: ECR_IMAGE (registry/repository), IMAGE_TAG, AWS_REGION.
set -euo pipefail

: "${ECR_IMAGE:?ECR_IMAGE is required}"
: "${IMAGE_TAG:?IMAGE_TAG is required}"
: "${AWS_REGION:?AWS_REGION is required}"

PARAMETERS_PATH='/peru-town-hub/stage/'
HEALTH_URL='http://localhost/api/health/'
COMPOSE=(docker compose -f docker-compose.stage.yml)

cd "$(dirname "$0")"
export ECR_IMAGE IMAGE_TAG

echo "Writing .env from Parameter Store ($PARAMETERS_PATH)"
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

echo "Logging in to ECR"
aws ecr get-login-password --region "$AWS_REGION" \
    | docker login --username AWS --password-stdin "${ECR_IMAGE%%/*}"

echo "Deploying $ECR_IMAGE:$IMAGE_TAG"
"${COMPOSE[@]}" pull
"${COMPOSE[@]}" up -d --wait db
"${COMPOSE[@]}" run --rm web python manage.py migrate --noinput
"${COMPOSE[@]}" up -d --remove-orphans

echo "Checking $HEALTH_URL"
for attempt in $(seq 1 10); do
    if curl --fail --silent --show-error "$HEALTH_URL"; then
        echo
        echo "Deploy succeeded"
        docker image prune --force
        exit 0
    fi
    echo "Health check attempt $attempt failed, retrying..."
    sleep 3
done

echo "Deploy failed: health check did not pass" >&2
"${COMPOSE[@]}" logs --tail 50 web >&2
exit 1
