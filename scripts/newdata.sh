#!/usr/bin/env bash
# Wipe database and start fresh with demo data seeded.
# Run: ./scripts/newdata.sh
# Or:  docker compose down -v && SEED_ON_STARTUP=true docker compose up --build

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Stopping containers and removing database volume..."
docker compose down -v

echo "Starting with fresh data (SEED_ON_STARTUP=true)..."
SEED_ON_STARTUP=true docker compose up --build "$@"
