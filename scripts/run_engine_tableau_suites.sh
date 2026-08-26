#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
QS_REPO=${QS_REPO:-$(cd "$ROOT_DIR/.." && pwd)/quantastream}
ENGINE=${ENGINE:-proxy}
MYSQL_HOST=${MYSQL_HOST:-127.0.0.1}
MYSQL_PORT=${MYSQL_PORT:-4000}
MYSQL_USER=${MYSQL_USER:-qstream}
MYSQL_PASSWORD=${MYSQL_PASSWORD:-}
MYSQL_DB=${MYSQL_DB:-quanta}
MYSQL_DSN=${MYSQL_DSN:-}
CONSUL_ADDR=${CONSUL_ADDR:-127.0.0.1:8500}
BENCHMARK_RUNS=${BENCHMARK_RUNS:-0}
REPORT_DIR=${REPORT_DIR:-}
TABLEAU_SUITES=${TABLEAU_SUITES:-mysql_compat_tableau_metadata.yaml mysql_compat_tableau_worksheets.yaml mysql_compat_tableau_custom_sql.yaml}

if [[ ! -d "$QS_REPO/sqlrunner" ]]; then
  echo "QuantaStream repo not found at QS_REPO=$QS_REPO" >&2
  echo "Set QS_REPO=/path/to/quantastream and retry." >&2
  exit 2
fi

if [[ -n "$REPORT_DIR" ]]; then
  mkdir -p "$REPORT_DIR"
fi

cd "$QS_REPO/sqlrunner"

common_args=(
  -engine "$ENGINE"
  -precise_timing
)

case "$ENGINE" in
  mysql-reference)
    if [[ -z "$MYSQL_DSN" ]]; then
      echo "ENGINE=mysql-reference requires MYSQL_DSN." >&2
      exit 2
    fi
    common_args+=(-mysql_dsn "$MYSQL_DSN")
    ;;
  inabox-direct|distributed)
    common_args+=(-consul "$CONSUL_ADDR")
    ;;
  *)
    common_args+=(
      -host "$MYSQL_HOST"
      -port "$MYSQL_PORT"
      -user "$MYSQL_USER"
      -db "$MYSQL_DB"
    )
    if [[ -n "$MYSQL_PASSWORD" ]]; then
      common_args+=(-password "$MYSQL_PASSWORD")
    fi
    ;;
esac

for suite in $TABLEAU_SUITES; do
  suite_path="sqltests/$suite"
  if [[ ! -f "$suite_path" ]]; then
    echo "Missing engine suite: $QS_REPO/sqlrunner/$suite_path" >&2
    exit 2
  fi

  args=("${common_args[@]}" -suite_file "$suite_path")
  if [[ "$BENCHMARK_RUNS" != "0" ]]; then
    args+=(
      -benchmark_runs "$BENCHMARK_RUNS"
      -benchmark_profile "tableau-${suite%.yaml}-${ENGINE}"
    )
    if [[ -n "$REPORT_DIR" ]]; then
      args+=(-benchmark_report "$REPORT_DIR/${suite%.yaml}-${ENGINE}.json")
    fi
  fi

  echo "== $suite ($ENGINE) =="
  go run . "${args[@]}"
done