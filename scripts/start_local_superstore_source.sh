#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
QS_REPO=${QS_REPO:-$(cd "$ROOT_DIR/../quantastream" 2>/dev/null && pwd)}
RUN_DIR=${RUN_DIR:-/tmp/qs-tableau-superstore}
DATA_DIR=${DATA_DIR:-$RUN_DIR/data}
RUNTIME_CONFIG_DIR=${RUNTIME_CONFIG_DIR:-$RUN_DIR/config}
QS_LOG=${QS_LOG:-$RUN_DIR/quantastream.log}
LOADER_LOG=${LOADER_LOG:-$RUN_DIR/qstream-loader.log}
MYSQL_HOST=${MYSQL_HOST:-127.0.0.1}
MYSQL_PORT=${MYSQL_PORT:-4000}
MYSQL_USER=${MYSQL_USER:-qstream}
MYSQL_DB=${MYSQL_DB:-quanta}
NATIVE_GRPC_HOST=${NATIVE_GRPC_HOST:-127.0.0.1}
NATIVE_GRPC_PORT=${NATIVE_GRPC_PORT:-4100}
LOADER_LISTEN=${LOADER_LISTEN:-127.0.0.1:8088}
LOADER_WORKERS=${LOADER_WORKERS:-4}
LOADER_CHANNEL_SIZE=${LOADER_CHANNEL_SIZE:-100000}
LOADER_FLUSH_INTERVAL=${LOADER_FLUSH_INTERVAL:-500ms}
RESET_DATA=${RESET_DATA:-1}

if [[ -z "${QS_REPO:-}" || ! -d "$QS_REPO" ]]; then
  echo "QS_REPO does not point at a QuantaStream checkout: ${QS_REPO:-<empty>}" >&2
  exit 2
fi

if [[ ! -d "$ROOT_DIR/configuration/superstore_orders" ]]; then
  echo "missing Superstore schema at $ROOT_DIR/configuration/superstore_orders" >&2
  exit 2
fi

mkdir -p "$RUN_DIR"
if [[ "$RESET_DATA" == "1" ]]; then
  rm -rf "$DATA_DIR" "$RUNTIME_CONFIG_DIR"
fi
mkdir -p "$DATA_DIR" "$RUNTIME_CONFIG_DIR"
cp -R "$ROOT_DIR/configuration/superstore_orders" "$RUNTIME_CONFIG_DIR/"

# Keep the helper intentionally local: it owns the configured demo ports only.
kill_listener_on_port() {
  local port=$1
  local pids
  pids=$(ss -ltnp "sport = :$port" 2>/dev/null | sed -n "s/.*pid=\([0-9]\+\).*/\1/p" | sort -u)
  if [[ -n "$pids" ]]; then
    kill $pids 2>/dev/null || true
  fi
}

loader_port=${LOADER_LISTEN##*:}
kill_listener_on_port "$MYSQL_PORT"
kill_listener_on_port "$NATIVE_GRPC_PORT"
kill_listener_on_port "$loader_port"
sleep 1

(
  cd "$QS_REPO"
  nohup env \
    QUANTASTREAM_CONFIG_DIR="$RUNTIME_CONFIG_DIR" \
    QUANTASTREAM_DATA_DIR="$DATA_DIR" \
    QUANTASTREAM_WAL_PATH="$DATA_DIR/storage.wal" \
    QUANTASTREAM_BIND="$MYSQL_HOST" \
    QUANTASTREAM_MYSQL_PORT="$MYSQL_PORT" \
    QUANTASTREAM_NATIVE_GRPC_BIND="$NATIVE_GRPC_HOST" \
    QUANTASTREAM_NATIVE_GRPC_PORT="$NATIVE_GRPC_PORT" \
    QUANTASTREAM_DATABASE="$MYSQL_DB" \
    QUANTASTREAM_MYSQL_COMMAND_TRACE=true \
    ./startup-scripts/start-standard.sh \
    > "$QS_LOG" 2>&1 < /dev/null &
  echo "quantastream_pid=$!"
)

for _ in $(seq 1 60); do
  if mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" -u "$MYSQL_USER" -D "$MYSQL_DB" -e "select 1" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" -u "$MYSQL_USER" -D "$MYSQL_DB" -e "select 1" >/dev/null 2>&1; then
  echo "QuantaStream did not become ready; tailing $QS_LOG" >&2
  tail -80 "$QS_LOG" >&2 || true
  exit 1
fi

(
  cd "$QS_REPO"
  nohup go run ./cmd/quantastream-loader \
    -connection-mode standard-native \
    -native-grpc-addr "$NATIVE_GRPC_HOST:$NATIVE_GRPC_PORT" \
    -config-dir "$RUNTIME_CONFIG_DIR" \
    -tables superstore_orders \
    -listen "$LOADER_LISTEN" \
    -workers "$LOADER_WORKERS" \
    -channel-size "$LOADER_CHANNEL_SIZE" \
    -flush-interval "$LOADER_FLUSH_INTERVAL" \
    > "$LOADER_LOG" 2>&1 < /dev/null &
  echo "loader_pid=$!"
)

for _ in $(seq 1 60); do
  if curl -fsS "http://$LOADER_LISTEN/healthz" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! curl -fsS "http://$LOADER_LISTEN/healthz" >/dev/null 2>&1; then
  echo "qstream-loader did not become ready; tailing $LOADER_LOG" >&2
  tail -80 "$LOADER_LOG" >&2 || true
  exit 1
fi

mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" -u "$MYSQL_USER" -D "$MYSQL_DB" -e "show tables;"
curl -fsS "http://$LOADER_LISTEN/healthz"
echo
echo "logs: $QS_LOG $LOADER_LOG"
