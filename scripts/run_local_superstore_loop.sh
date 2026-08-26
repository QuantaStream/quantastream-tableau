#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
MYSQL_HOST=${MYSQL_HOST:-127.0.0.1}
MYSQL_PORT=${MYSQL_PORT:-4000}
MYSQL_USER=${MYSQL_USER:-qstream}
MYSQL_DB=${MYSQL_DB:-quanta}
LOADER_TARGET=${LOADER_TARGET:-http://127.0.0.1:8088/ingest/json}
BATCH_SIZE=${BATCH_SIZE:-4}
WORKERS=${WORKERS:-1}
SAMPLE_CSV=${SAMPLE_CSV:-$ROOT_DIR/samples/superstore/synthetic_orders.csv}

"$ROOT_DIR/scripts/start_local_superstore_source.sh"

"$ROOT_DIR/scripts/load_superstore_csv.py" \
  -target "$LOADER_TARGET" \
  -batch-size "$BATCH_SIZE" \
  -workers "$WORKERS" \
  "$SAMPLE_CSV"

MYSQL_HOST="$MYSQL_HOST" \
MYSQL_PORT="$MYSQL_PORT" \
MYSQL_USER="$MYSQL_USER" \
MYSQL_DB="$MYSQL_DB" \
  "$ROOT_DIR/scripts/run_superstore_smoke.sh"

curl -fsS http://127.0.0.1:8088/stats | python3 -m json.tool | head -80
