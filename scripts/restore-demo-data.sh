#!/usr/bin/env sh
# Restore the SavePoint demo data package (full catalogue + demo accounts) into the local
# Docker Compose database, then start the application.
#
# Usage: scripts/restore-demo-data.sh <savepoint-demo-data-vX.Y.Z.dump>
#
# It replaces the contents of the local database. The package is a PostgreSQL custom-format
# dump published as an asset of the GitHub release. Set COMPOSE_ARGS to use another compose
# file (default: "-f infra/compose.yaml") and COMPOSE_PROJECT_NAME to use another project.
set -eu

# Stop Git Bash on Windows from rewriting the /tmp paths passed to the container.
export MSYS_NO_PATHCONV=1

DUMP="${1:?Usage: scripts/restore-demo-data.sh <savepoint-demo-data-vX.Y.Z.dump>}"
COMPOSE_ARGS="${COMPOSE_ARGS:--f infra/compose.yaml}"
DB_USER="savepoint_test"
DB_NAME="savepoint_test"
IN_CONTAINER="/tmp/savepoint-demo-data.dump"

[ -f "$DUMP" ] || { echo "File not found: $DUMP" >&2; exit 1; }

if [ -f "$DUMP.sha256" ]; then
  echo "Checking the SHA-256 of the package..."
  expected=$(cut -d' ' -f1 "$DUMP.sha256")
  if command -v sha256sum >/dev/null 2>&1; then
    actual=$(sha256sum "$DUMP" | cut -d' ' -f1)
  else
    actual=$(shasum -a 256 "$DUMP" | cut -d' ' -f1)
  fi
  [ "$expected" = "$actual" ] || { echo "SHA-256 mismatch: expected $expected, got $actual" >&2; exit 1; }
fi

# shellcheck disable=SC2086
dc() { docker compose $COMPOSE_ARGS "$@"; }

echo "Stopping the application (the database volume is kept)..."
dc down
dc up -d --wait db

echo "Recreating the database..."
dc exec -T db dropdb -U "$DB_USER" --if-exists "$DB_NAME"
dc exec -T db createdb -U "$DB_USER" "$DB_NAME"

echo "Restoring the package (this takes a few minutes)..."
dc cp "$DUMP" "db:$IN_CONTAINER"
dc exec -T db pg_restore -U "$DB_USER" -d "$DB_NAME" --no-owner --exit-on-error "$IN_CONTAINER"
dc exec -T db rm -f "$IN_CONTAINER"

echo "Starting the application..."
dc up --build --wait
echo "Done. Open http://localhost:3000/es"
