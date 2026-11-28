#!/bin/bash
# Deploys an image tag to the stage EC2 through SSM Run Command, giving it the last
# stable version to roll back to; records the tag as stable when the deploy succeeds.
# Runs on the CI runner with AWS credentials already configured.
# Required env: AWS_REGION, ECR_REPOSITORY, DEPLOY_BUCKET, IMAGE_TAG, DEPLOY_EVENT
# (push uploads the tag's compose; a manual redeploy uses the one already in S3).
set -euo pipefail

: "${AWS_REGION:?AWS_REGION is required}"
: "${ECR_REPOSITORY:?ECR_REPOSITORY is required}"
: "${DEPLOY_BUCKET:?DEPLOY_BUCKET is required}"
: "${IMAGE_TAG:?IMAGE_TAG is required}"
: "${DEPLOY_EVENT:?DEPLOY_EVENT is required}"

S3_PREFIX="s3://$DEPLOY_BUCKET/stage"
STABLE_PARAMETER='/peru-town-hub/deploy/stage/stable-image-tag'
REMOTE_DIR='/opt/peru-town-hub'
EXECUTION_TIMEOUT_SECONDS=900
POLL_SECONDS=10
# A minute past SSM's own timeout, so its TimedOut status is the one read.
MAX_POLLS=$(((EXECUTION_TIMEOUT_SECONDS + 60) / POLL_SECONDS))
IMAGE_TAG_PATTERN='^sha-[0-9a-f]{40}$'
SUMMARY=${GITHUB_STEP_SUMMARY:-/dev/null}

cd "$(dirname "$0")/../.."

valid_tag() {
    [[ "$1" =~ $IMAGE_TAG_PATTERN ]]
}

if ! valid_tag "$IMAGE_TAG"; then
    echo "::error::Invalid image tag '$IMAGE_TAG'. Expected sha- followed by the full 40-character commit SHA."
    exit 1
fi

account_id=$(aws sts get-caller-identity --query Account --output text)
ecr_image="$account_id.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY"

echo "Checking that $IMAGE_TAG exists in $ECR_REPOSITORY"
if ! scripts/ci/ecr-image-exists.sh "$ECR_REPOSITORY" "$IMAGE_TAG"; then
    echo "::error::Image tag $IMAGE_TAG not found in $ECR_REPOSITORY"
    exit 1
fi

echo "Reading the stable version ($STABLE_PARAMETER)"
stable_tag=''
if output=$(aws ssm get-parameter --name "$STABLE_PARAMETER" \
    --query Parameter.Value --output text 2>&1); then
    stable_tag=$output
elif [[ "$output" == *ParameterNotFound* ]]; then
    echo "::warning::No stable version recorded: a failure will need a fix forward."
else
    echo "::error::Could not read $STABLE_PARAMETER: $output"
    exit 1
fi
if [ -n "$stable_tag" ]; then
    if ! valid_tag "$stable_tag"; then
        echo "::error::Invalid stable version in $STABLE_PARAMETER. Expected sha- followed by the full 40-character commit SHA."
        exit 1
    fi
    if ! scripts/ci/ecr-image-exists.sh "$ECR_REPOSITORY" "$stable_tag"; then
        echo "::warning::The stable version $stable_tag is no longer in ECR: a failure will need a fix forward."
        stable_tag=''
    fi
fi
echo "Stable version: ${stable_tag:-none}"

echo "Uploading deploy files to $S3_PREFIX"
if [ "$DEPLOY_EVENT" = 'push' ]; then
    aws s3 cp docker-compose.stage.yml "$S3_PREFIX/$IMAGE_TAG/docker-compose.stage.yml"
fi
aws s3 cp scripts/deploy.sh "$S3_PREFIX/deploy.sh"

instance_ids=$(aws ec2 describe-instances \
    --filters Name=tag:Env,Values=stage Name=instance-state-name,Values=running \
    --query 'Reservations[].Instances[].InstanceId' --output text)
read -r -a instances <<< "$instance_ids"
if [ "${#instances[@]}" -ne 1 ]; then
    echo "::error::Expected 1 running EC2 instance tagged Env=stage, found ${#instances[@]}. Start it and re-run."
    exit 1
fi
instance_id=${instances[0]}

# SSM runs as root with a minimal PATH; the AWS CLI is a snap.
ssm_parameters=$(jq -n \
    --arg timeout "$EXECUTION_TIMEOUT_SECONDS" \
    --arg prefix "$S3_PREFIX" \
    --arg dir "$REMOTE_DIR" \
    --arg image "$ecr_image" \
    --arg tag "$IMAGE_TAG" \
    --arg stable "$stable_tag" \
    --arg region "$AWS_REGION" \
    '{
        executionTimeout: [$timeout],
        commands: [
            "set -eu",
            "export PATH=\"$PATH:/snap/bin\"",
            "cd \($dir)",
            "aws s3 cp --only-show-errors \($prefix)/deploy.sh .",
            "chmod +x deploy.sh",
            "ECR_IMAGE=\($image) IMAGE_TAG=\($tag) STABLE_TAG=\($stable) AWS_REGION=\($region) S3_PREFIX=\($prefix) ./deploy.sh"
        ]
    }')

command_id=$(aws ssm send-command \
    --instance-ids "$instance_id" \
    --document-name AWS-RunShellScript \
    --comment "Deploy $IMAGE_TAG" \
    --parameters "$ssm_parameters" \
    --query 'Command.CommandId' --output text)
echo "Running deploy.sh on $instance_id (command $command_id)"

status='Pending'
for _ in $(seq 1 "$MAX_POLLS"); do
    sleep "$POLL_SECONDS"
    status=$(aws ssm get-command-invocation \
        --command-id "$command_id" --instance-id "$instance_id" \
        --query Status --output text 2>/dev/null || echo 'Pending')
    case "$status" in
        Pending | InProgress | Delayed) ;;
        *) break ;;
    esac
done

invocation() {
    aws ssm get-command-invocation \
        --command-id "$command_id" --instance-id "$instance_id" \
        --query "$1" --output text
}
stdout=$(invocation StandardOutputContent)
echo "::group::deploy.sh output"
echo "$stdout"
invocation StandardErrorContent
echo "::endgroup::"

case "$status" in
    Success | Failed) result=$(grep '^Deploy result: ' <<< "$stdout" | tail -n 1 || true) ;;
    *) result="Deploy result: Timed out or interrupted (status $status): check stage by hand (deploy runbook)." ;;
esac
result=${result:-"Deploy result: Unknown (status $status): check stage by hand (deploy runbook)."}
echo "$result" >> "$SUMMARY"

if [ "$status" != 'Success' ]; then
    echo "::error::$result"
    exit 1
fi

echo "Recording $IMAGE_TAG as the stable version"
if ! aws ssm put-parameter --name "$STABLE_PARAMETER" --value "$IMAGE_TAG" \
    --overwrite > /dev/null; then
    echo "::error::$IMAGE_TAG is running, but it could not be recorded as stable: the stable version is still ${stable_tag:-none}."
    exit 1
fi
echo "Deployed $ecr_image:$IMAGE_TAG to stage"
