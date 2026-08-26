#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
MYSQL_HOST=${MYSQL_HOST:-127.0.0.1}
MYSQL_PORT=${MYSQL_PORT:-4000}
MYSQL_USER=${MYSQL_USER:-qstream}
MYSQL_DB=${MYSQL_DB:-quanta}
MYSQL_PASSWORD=${MYSQL_PASSWORD:-}
QUERY_FILE=${QUERY_FILE:-$ROOT_DIR/queries/superstore_smoke.sql}

mysql_args=(
  -h "$MYSQL_HOST"
  -P "$MYSQL_PORT"
  -u "$MYSQL_USER"
  -D "$MYSQL_DB"
  --table
)

if [[ -n "$MYSQL_PASSWORD" ]]; then
  mysql_args+=(-p"$MYSQL_PASSWORD")
fi

sed "/^[[:space:]]*--/d" "$QUERY_FILE" | mysql "${mysql_args[@]}"
