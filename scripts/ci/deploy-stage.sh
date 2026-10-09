#!/bin/bash
# Deploys an image tag to the stage EC2 through SSM Run Command.
# Runs on the CI runner with AWS credentials already configured.
# Required env: AWS_REGION, ECR_REPOSITORY, DEPLOY_BUCKET, IMAGE_TAG.
set -euo pipefail

: "${AWS_REGION:?AWS_REGION is required}"
: "${ECR_REPOSITORY:?ECR_REPOSITORY is required}"
: "${DEPLOY_BUCKET:?DEPLOY_BUCKET is required}"
: "${IMAGE_TAG:?IMAGE_TAG is required}"

S3_PREFIX="s3://$DEPLOY_BUCKET/stage"
REMOTE_DIR='/opt/peru-town-hub'
POLL_SECONDS=10
MAX_POLLS=90

cd "$(dirname "$0")/../.."

account_id=$(aws sts get-caller-identity --query Account --output text)
ecr_image="$account_id.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY"

echo "Checking that $IMAGE_TAG exists in $ECR_REPOSITORY"
found=$(aws ecr batch-get-image \
    --repository-name "$ECR_REPOSITORY" \
    --image-ids imageTag="$IMAGE_TAG" \
    --query 'length(images)' --output text)
if [ "$found" -eq 0 ]; then
    echo "::error::Image tag $IMAGE_TAG not found in $ECR_REPOSITORY"
    exit 1
fi

echo "Uploading deploy files to $S3_PREFIX"
aws s3 cp docker-compose.stage.yml "$S3_PREFIX/docker-compose.stage.yml"
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
    --arg prefix "$S3_PREFIX" \
    --arg dir "$REMOTE_DIR" \
    --arg image "$ecr_image" \
    --arg tag "$IMAGE_TAG" \
    --arg region "$AWS_REGION" \
    '{
        executionTimeout: ["900"],
        commands: [
            "set -eu",
            "export PATH=\"$PATH:/snap/bin\"",
            "cd \($dir)",
            "aws s3 cp \($prefix)/docker-compose.stage.yml .",
            "aws s3 cp \($prefix)/deploy.sh .",
            "chmod +x deploy.sh",
            "ECR_IMAGE=\($image) IMAGE_TAG=\($tag) AWS_REGION=\($region) ./deploy.sh"
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

echo "::group::deploy.sh output"
aws ssm get-command-invocation \
    --command-id "$command_id" --instance-id "$instance_id" \
    --query '[StandardOutputContent, StandardErrorContent]' --output text
echo "::endgroup::"

if [ "$status" != 'Success' ]; then
    echo "::error::Deploy finished with status: $status"
    exit 1
fi
echo "Deployed $ecr_image:$IMAGE_TAG to stage"
