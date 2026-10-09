#!/bin/bash
# Exits 0 if the tag exists in the ECR repository, 1 otherwise.
# Usage: ecr-image-exists.sh <repository> <tag>
set -euo pipefail

repository=${1:?repository is required}
tag=${2:?tag is required}

found=$(aws ecr batch-get-image \
    --repository-name "$repository" \
    --image-ids imageTag="$tag" \
    --query 'length(images)' --output text)

[ "$found" -gt 0 ]
