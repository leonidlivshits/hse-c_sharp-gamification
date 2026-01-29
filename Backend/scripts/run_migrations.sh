#!/usr/bin/env bash
set -euo pipefail
# Run Alembic migrations in local/dev (reads .env)
# Ensure .env is present or DATABASE_URL exported

# Load .env variables into environment (simple loader; requires no blank lines or export syntax)
if [ -f .env ]; then
  # shellcheck disable=SC2046
  export $(grep -v '^#' .env | xargs)
fi

# run alembic
alembic upgrade head
