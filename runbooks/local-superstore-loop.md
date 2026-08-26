# Local Superstore Loop

This is the smallest end-to-end loop before Tableau Desktop enters the picture.
It uses synthetic Superstore-shaped data committed in this repository so the
loader, schema, and SQL smoke queries can be tested without downloading Tableau
sample files first.

## 1. Start QuantaStream And qstream-loader

Follow the startup steps in [Tableau Desktop Smoke](tableau-desktop-smoke.md)
through the loader health check.

## 2. Load Synthetic Superstore Rows

```bash
scripts/load_superstore_csv.py \
  -target http://127.0.0.1:8088/ingest/json \
  -batch-size 4 \
  -workers 1 \
  samples/superstore/synthetic_orders.csv
```

Expected stderr shape:

```text
file=samples/superstore/synthetic_orders.csv rows=8 emitted=8 accepted=8 failed=0 elapsed=...
```

## 3. Run Smoke Queries

```bash
scripts/run_superstore_smoke.sh
```

Override connection settings with environment variables if needed:

```bash
MYSQL_HOST=127.0.0.1 MYSQL_PORT=4000 MYSQL_USER=qstream MYSQL_DB=quanta \
  scripts/run_superstore_smoke.sh
```

## 4. What This Proves

This loop proves:

- the Superstore schema can be loaded into QuantaStream;
- `qstream-loader` accepts Superstore-shaped JSON events;
- core Tableau worksheet query shapes work through the MySQL endpoint;
- the repo has a deterministic test path that does not depend on bundled
  Tableau sample data.

It does not prove Tableau compatibility by itself. The next step is still to
connect Tableau Desktop and capture its actual generated SQL.
