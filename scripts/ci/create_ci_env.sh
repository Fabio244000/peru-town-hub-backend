#!/bin/bash
# Writes the CI .env from .env.example with random secrets: CI uses no repository
# secrets (conventions/security.md, §6). Never overwrites an existing .env.
set -euo pipefail

cd "$(dirname "$0")/../.."

if [ -e .env ]; then
    echo '.env already exists; refusing to overwrite it' >&2
    exit 1
fi

random_value() {
    python3 -c 'import secrets; print(secrets.token_urlsafe(50))'
}

while IFS= read -r line; do
    if [[ $line =~ ^([A-Z0-9_]+)=$ ]]; then
        printf '%s=%s\n' "${BASH_REMATCH[1]}" "$(random_value)"
    else
        printf '%s\n' "$line"
    fi
done < .env.example > .env
chmod 600 .env
