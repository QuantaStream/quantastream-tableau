# QuantaStream Tableau

This repository contains Tableau integration assets for QuantaStream.

The first integration target is Tableau Desktop using Tableau's native MySQL
connector against the QuantaStream MySQL-compatible endpoint. The goal is to
make Tableau connect, browse schemas, preview rows, run worksheets, exercise
custom SQL, and eventually validate extract behavior against realistic
QuantaStream data sets.

## Current Focus

The first compliance-oriented target is Tableau's Sample Superstore data. That
keeps the early work aligned with a dataset Tableau users already recognize,
while QuantaStream's radiosport data remains a stronger showcase path for public
dashboards and streaming/bitmap-native storytelling.

Start here:

- [Compatibility plan](docs/COMPATIBILITY_PLAN.md)
- [Tableau Desktop smoke runbook](runbooks/tableau-desktop-smoke.md)
- [Superstore sample notes](samples/superstore/README.md)
- [Superstore QuantaStream schema](configuration/superstore_orders/schema.yaml)

## Repository Layout

- captures/: sanitized Tableau SQL capture notes and trace summaries.
- configuration/: QuantaStream schemas used for Tableau testing.
- docs/: compatibility and integration plans.
- runbooks/: manual smoke-test procedures.
- samples/: dataset notes; sample data is not vendored.
- scripts/: small local helpers for preparing test data.

## Data Preparation Helpers

The Superstore path starts with two plain Python helpers:

```bash
scripts/normalize_superstore_csv.py input.csv /tmp/superstore_orders_normalized.csv
scripts/load_superstore_csv.py -target http://127.0.0.1:8088/ingest/json input.csv
scripts/summarize_mysql_trace.py /tmp/quantastream-tableau.log > captures/tableau-smoke-summary.md
scripts/trace_to_sqlrunner.py /tmp/quantastream-tableau.log \
  > captures/sqlrunner/mysql_compat_tableau_capture.yaml
scripts/run_engine_tableau_suites.sh
```

The loader helper accepts either original Tableau headers or normalized
snake_case headers and posts event batches to `qstream-loader`. The trace
summary helper consumes QuantaStream `MYSQL_COMMAND_TRACE` logs emitted by the
engine when command tracing is enabled. The SQLRunner helper turns the same
capture into a draft replay suite for cleanup and migration into the engine
repo. The engine-suite helper runs the curated Tableau replay suites that now
live under `quantastream/sqlrunner/sqltests`, including connect and extract smoke probes.

## Scope

Planned contents include:

- Tableau connection and smoke-test runbooks;
- captured Tableau-generated SQL;
- SQLRunner replay-suite notes for Tableau compatibility;
- engine replay-suite runner for connect, metadata, worksheet, custom SQL, and extract smoke;
- sample dashboards or workbook assets built from QuantaStream sample data;
- Tableau Datasource Verification Tool notes and results;
- connector experiments if a dedicated Tableau connector becomes useful later.

This repository should not contain QuantaStream engine code, Tableau binaries,
private customer data, or unsanitized connection logs.

## Licensing

The contents of this repository are licensed under the Apache License 2.0. See
[LICENSE](LICENSE).

QuantaStream itself is licensed separately under the Elastic License 2.0. This
repository is intentionally focused on integration assets, examples, and
compatibility harnesses rather than the core database engine.

## Status

This repository is new. The near-term path is practical and capture-driven:

1. Prepare and load Tableau Sample Superstore into QuantaStream.
2. Connect Tableau Desktop through the built-in MySQL connector.
3. Capture real Tableau-generated SQL for connect, metadata, previews,
   worksheets, custom SQL, and extract smoke.
4. Convert stable captured SQL into SQLRunner compatibility suites in the
   QuantaStream engine repo.
5. Use Tableau verification tooling later as an external compatibility pressure
   test.

## Related Repositories

- [QuantaStream](https://github.com/QuantaStream/quantastream)
- [QuantaStream website](https://github.com/QuantaStream/QuantaStream.github.io)

## Local Synthetic Smoke

For a deterministic end-to-end check before Tableau Desktop is installed, use
runbooks/local-superstore-loop.md. It loads the small synthetic Superstore-shaped
CSV in samples/superstore/synthetic_orders.csv and runs the SQL smoke pack in
queries/superstore_smoke.sql.

For the engine-side Tableau replay suites, use:

```bash
scripts/run_engine_tableau_suites.sh
```

By default this expects the QuantaStream engine repo at `../quantastream` and a
local MySQL-compatible QS endpoint on `127.0.0.1:4000`. Override `QS_REPO`,
`ENGINE`, `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, or
`CONSUL_ADDR` as needed.
