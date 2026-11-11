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

sed '/^DJANGO_SECRET_KEY=/d; /^POSTGRES_PASSWORD=/d' .env.example > .env
printf 'DJANGO_SECRET_KEY=%s\nPOSTGRES_PASSWORD=%s\n' "$(random_value)" "$(random_value)" >> .env
chmod 600 .env
