# QuantaStream Tableau

This repository contains Tableau integration assets for QuantaStream.

The first integration target is Tableau Desktop using Tableau's
**Other Databases (JDBC)** path with the MySQL JDBC driver against the
QuantaStream MySQL-compatible endpoint. The goal is to make Tableau connect,
browse schemas, preview rows, run worksheets, exercise custom SQL, and
eventually validate extract behavior against realistic QuantaStream data sets.

Do not use Tableau's built-in MySQL connector for the current preview loop.
Use the generic JDBC connector and a MySQL JDBC URL instead.

## Current Focus

The first compliance-oriented target is Tableau's Sample Superstore data. That
keeps the early work aligned with a dataset Tableau users already recognize,
while QuantaStream's radiosport data remains a stronger showcase path for public
dashboards and streaming/bitmap-native storytelling.

Start here:

- [Compatibility plan](docs/COMPATIBILITY_PLAN.md)
- [Tableau Desktop smoke runbook](runbooks/tableau-desktop-smoke.md)
- [TPC-H Tableau views](runbooks/tpch-tableau-views.md)
- [Superstore sample notes](samples/superstore/README.md)
- [Superstore QuantaStream schema](configuration/superstore_orders/schema.yaml)

## Repository Layout

- captures/: sanitized Tableau SQL capture notes and trace summaries.
- configuration/: QuantaStream table and view schemas used for Tableau testing.
- docs/: compatibility and integration plans.
- runbooks/: manual smoke-test procedures.
- samples/: dataset notes; sample data is not vendored.
- scripts/: small local helpers for preparing test data.

## Data Preparation Helpers

The Superstore path uses small shell and Python helpers:

```bash
scripts/normalize_superstore_csv.py input.csv /tmp/superstore_orders_normalized.csv
scripts/start_local_superstore_source.sh
scripts/run_local_superstore_loop.sh
scripts/load_superstore_csv.py -target http://127.0.0.1:8088/ingest/json input.csv
scripts/summarize_mysql_trace.py /tmp/quantastream-tableau.log > captures/tableau-smoke-summary.md
scripts/trace_to_sqlrunner.py /tmp/quantastream-tableau.log --classify \
  > captures/sqlrunner/mysql_compat_tableau_capture.yaml
scripts/trace_to_sqlrunner.py /tmp/quantastream-tableau.log \
  --split-by-phase --out-dir captures/sqlrunner/generated
scripts/run_engine_tableau_suites.sh
```

The local Superstore helpers start a source-tree QuantaStream server, stage the
Superstore schema, launch `qstream-loader`, load the committed synthetic sample,
and run worksheet-style smoke SQL. The loader helper accepts either original
Tableau headers or normalized snake_case headers and posts event batches to
`qstream-loader`. The trace summary helper consumes QuantaStream
`MYSQL_COMMAND_TRACE` logs emitted by the engine when command tracing is
enabled. The SQLRunner helper turns the same
capture into a draft replay suite for cleanup and migration into the engine
repo. Use `--classify` or `--split-by-phase` to bucket captured SQL into
connect, metadata, worksheet, custom SQL, and extract suites. The engine-suite
helper runs the curated Tableau replay suites that now live under
`quantastream/sqlrunner/sqltests`; by default it targets the local Superstore
loop with connection, metadata, and worksheet queries.

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
2. Connect Tableau Desktop through **Other Databases (JDBC)**.
3. Capture real Tableau-generated SQL for connect, metadata, previews,
   worksheets, custom SQL, and extract smoke.
4. Convert stable captured SQL into SQLRunner compatibility suites in the
   QuantaStream engine repo.
5. Use Tableau verification tooling later as an external compatibility pressure
   test.

## Current Tableau Notes

- Use Tableau's generic JDBC connector with the MySQL Connector/J driver.
- The current Windows smoke path used Oracle MySQL Connector/J `8.4.0`,
  installed separately under `C:\Program Files\Tableau\Drivers`.
- Manual relationships work. Automatic relationship inference is not expected
  in the current preview because Tableau's generic JDBC path reads table
  columns and primary keys but does not appear to request foreign-key discovery
  metadata during the drag/drop relationship flow.
- For TPC-H relationship tests, define relationships manually, for example
  `customer.c_custkey = orders.o_custkey` and
  `orders.o_orderkey = lineitem.l_orderkey`.
- For a smoother Tableau package, prefer curated views over asking users to
  recreate the same relationship graph. This repository includes
  `queries/tpch_tableau_views.sql`, which installs `q3_order_line_base` and the
  wider `tpch_order_line_sales_base` view.
- Do not model a Tableau relationship from a curated view to another physical
  table yet. Tableau may emit a `LEFT JOIN` against the view, and QuantaStream's
  current relationship-vector execution path only supports the inner-join slice
  there. Add the needed fields to the curated view instead.
- Keep `QUANTASTREAM_MYSQL_COMMAND_TRACE=true` enabled while capturing Tableau
  issues, then summarize or bundle the resulting QS trace log.

## Related Repositories

- [QuantaStream](https://github.com/QuantaStream/quantastream)
- [QuantaStream website](https://github.com/QuantaStream/QuantaStream.github.io)

## Local Synthetic Smoke

For a deterministic end-to-end check before Tableau Desktop is installed, use
runbooks/local-superstore-loop.md or run:

```bash
scripts/run_local_superstore_loop.sh
```

It starts a clean local source-tree QuantaStream instance, loads the small
synthetic Superstore-shaped CSV in samples/superstore/synthetic_orders.csv, and
runs the SQL smoke pack in queries/superstore_smoke.sql.

For the engine-side Tableau replay suites, use:

```bash
scripts/run_engine_tableau_suites.sh
```

By default this expects the QuantaStream engine repo at `../quantastream`, a
local MySQL-compatible QS endpoint on `127.0.0.1:4000`, and the Superstore
schema loaded as `superstore_orders`. The default engine is `inabox-standard`;
override `QS_REPO`, `ENGINE`, `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`,
`MYSQL_PASSWORD`, `CONSUL_ADDR`, or `TABLEAU_SUITES` as needed.
