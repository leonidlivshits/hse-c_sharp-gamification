#!/usr/bin/env bash
set -euo pipefail
# NOTE: Alembic must be configured before running migrations in production.
alembic upgrade head
