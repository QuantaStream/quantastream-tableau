#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
MYSQL_HOST=${MYSQL_HOST:-127.0.0.1}
MYSQL_PORT=${MYSQL_PORT:-4000}
MYSQL_USER=${MYSQL_USER:-qstream}
MYSQL_DB=${MYSQL_DB:-quanta}
LOADER_TARGET=${LOADER_TARGET:-http://127.0.0.1:8088/ingest/json}
LOADER_STATS_URL=${LOADER_STATS_URL:-${LOADER_TARGET%/ingest/json}/stats}
BATCH_SIZE=${BATCH_SIZE:-4}
WORKERS=${WORKERS:-1}
SAMPLE_CSV=${SAMPLE_CSV:-$ROOT_DIR/samples/superstore/synthetic_orders.csv}

wait_for_loader_idle() {
  local deadline=$((SECONDS + 30))
  local stats queued open flush_errors
  while (( SECONDS < deadline )); do
    if stats=$(curl -fsS "$LOADER_STATS_URL" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["router"]["total_queued"], d["router"]["open_session_count"], d["flush"]["error_count"])' 2>/dev/null); then
      read -r queued open flush_errors <<<"$stats"
      if [[ "$queued" == "0" && "$open" == "0" && "$flush_errors" == "0" ]]; then
        return 0
      fi
    fi
    sleep 1
  done
  echo "qstream-loader did not become idle; last stats: ${stats:-<unavailable>}" >&2
  return 1
}

"$ROOT_DIR/scripts/start_local_superstore_source.sh"

"$ROOT_DIR/scripts/load_superstore_csv.py" \
  -target "$LOADER_TARGET" \
  -batch-size "$BATCH_SIZE" \
  -workers "$WORKERS" \
  "$SAMPLE_CSV"

wait_for_loader_idle

MYSQL_HOST="$MYSQL_HOST" \
MYSQL_PORT="$MYSQL_PORT" \
MYSQL_USER="$MYSQL_USER" \
MYSQL_DB="$MYSQL_DB" \
  "$ROOT_DIR/scripts/run_superstore_smoke.sh"

curl -fsS http://127.0.0.1:8088/stats | python3 -m json.tool | head -80
