# QuantaStream Tableau

This repository is a Tableau integration lab for QuantaStream. You do not need
this repository to use Tableau with QuantaStream.

For ordinary Tableau Desktop usage, all you need is:

- a running QuantaStream server;
- Oracle MySQL Connector/J installed for Tableau;
- Tableau's **Other Databases (JDBC)** connector;
- a MySQL JDBC URL that points at QuantaStream's MySQL-compatible endpoint.

The executable compatibility contract lives in the main QuantaStream repository
under `sqlrunner/sqltests/mysql_compat_tableau_*.yaml`. This repository keeps
optional integration assets: runbooks, sample schemas, sanitized Tableau SQL
captures, helper scripts, and demo query/view packages.

## Quick Connect

1. Start QuantaStream with a MySQL-compatible endpoint, for example
   `127.0.0.1:4000`.
2. Install Oracle MySQL Connector/J for Tableau. The current Windows smoke path
   used MySQL Connector/J `8.4.0` under:

   ```text
   C:\Program Files\Tableau\Drivers\mysql-connector-j-8.4.0.jar
   ```

3. Restart Tableau Desktop after installing the driver.
4. In Tableau Desktop, choose **Other Databases (JDBC)**.
5. Use one of these JDBC URLs:

   ```text
   jdbc:mysql://127.0.0.1:4000/quanta?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC
   ```

   If Tableau runs on Windows and QuantaStream runs inside WSL, use:

   ```text
   jdbc:mysql://wsl.localhost:4000/quanta?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC
   ```

6. Use your configured QuantaStream username, for example `qstream`.
7. Select the `quanta` database, then choose a table or curated view.

Do not use Tableau's built-in MySQL connector for the current preview path. The
validated route is Tableau's generic JDBC connector plus MySQL Connector/J.

For production workbooks and reusable demos, prefer a curated QuantaStream view
over modeling directly from physical tables. Views provide a stable Tableau
contract with:

- business-friendly field names;
- no dependency on Tableau's relationship-inference behavior;
- unique projected column names that avoid duplicate-column alias collisions;
- natural business keys instead of internal relationship identifiers; and
- simpler workbooks that are less sensitive to changes in the underlying table
  schemas.

Physical tables remain useful for migration validation, troubleshooting, and
advanced users who deliberately want to construct their own Tableau data model.

## Load Sample Superstore

Tableau's Sample Superstore is its familiar demo/training dataset. This repo
does not vendor Tableau's original data, but it does provide a
Superstore-compatible QuantaStream schema and loader scripts so you can load
either:

- your own exported Sample Superstore Orders CSV; or
- the tiny synthetic Superstore-shaped CSV committed here for smoke testing.

The schema is:

```text
configuration/superstore_orders/schema.yaml
```

For the simplest local source-tree loop, put the QuantaStream checkout beside
this repo as `../quantastream`, then run:

```bash
SAMPLE_CSV=/path/to/sample-superstore-orders.csv \
  BATCH_SIZE=1000 \
  scripts/run_local_superstore_loop.sh
```

To use the committed synthetic smoke file instead:

```bash
scripts/run_local_superstore_loop.sh
```

That script starts QuantaStream, starts `qstream-loader`, loads the CSV into the
`superstore_orders` table, and runs a small smoke query pack. After that,
connect Tableau with the JDBC URL from the quick-connect section and choose
`superstore_orders`.

If QuantaStream and `qstream-loader` are already running, load a CSV directly:

```bash
scripts/load_superstore_csv.py \
  -target http://127.0.0.1:8088/ingest/json \
  -batch-size 1000 \
  -workers 1 \
  /path/to/sample-superstore-orders.csv
```

## When To Clone This Repo

Clone this repository if you want to reproduce or extend the Tableau
compatibility work: run the smoke runbooks, inspect sanitized Tableau SQL
captures, install curated demo views, or contribute new Tableau-driven test
cases back to QuantaStream.

If you only want to connect Tableau to QuantaStream, start with the main
QuantaStream repository and the quick-connect steps above.

## Current Focus

This lab has two jobs:

- keep Tableau-generated SQL captures and replay fixtures that help harden
  QuantaStream's Tableau compatibility;
- provide small examples, runbooks, and curated views for people who want to
  reproduce the integration work.

The first compliance-oriented target is Tableau's Sample Superstore data. That
keeps the early work aligned with a dataset Tableau users already recognize.

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

This repository may contain:

- Tableau connection and smoke-test runbooks;
- captured Tableau-generated SQL;
- notes for SQLRunner replay suites that are promoted into the main
  QuantaStream repository;
- an engine replay-suite runner for connect, metadata, worksheet, custom SQL,
  and extract smoke;
- sample dashboards or workbook assets built from QuantaStream sample data;
- Tableau Datasource Verification Tool notes and results;
- connector experiments if a dedicated Tableau connector becomes useful later.

This repository should not contain QuantaStream engine code, Tableau binaries,
private customer data, unsanitized connection logs, or the canonical
QuantaStream compatibility suites.

## Licensing

The contents of this repository are licensed under the Apache License 2.0. See
[LICENSE](LICENSE).

QuantaStream itself is licensed separately under the Elastic License 2.0. This
repository is intentionally focused on integration assets, examples, and
compatibility harnesses rather than the core database engine.

## Status

This repository is a companion lab. The near-term path is practical and
capture-driven:

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
- Treat curated views as the recommended Tableau-facing analytics contract.
  They provide stable business names, avoid dependence on relationship
  inference and duplicate-column aliases, expose natural keys instead of
  internal relationship identifiers, and keep workbooks simpler when physical
  schemas evolve. This repository includes
  `queries/tpch_tableau_views.sql`, which installs `q3_order_line_base` and the
  wider `tpch_order_line_sales_base` view.
- Do not model a Tableau relationship from a curated view to another physical
  table yet. Tableau may emit a `LEFT JOIN` against the view, and QuantaStream's
  current relationship-vector execution path only supports the inner-join slice
  there. Add the needed fields to the curated view instead.
- Tableau extract smoke has been validated through the generic JDBC path. The
  QuantaStream engine path requires SQL
  `NOW()`/`CURRENT_TIMESTAMP()` support and explicit UTC metadata
  (`@@system_time_zone=UTC`, `@@time_zone=+00:00`) so Tableau can compare
  extract and server time zones without a client warning.
- Current traces may contain non-blocking Tableau capability probes, including
  a one-column synthetic query grouped by ordinal `2` and `SHOW KEYS` against a
  view. Tableau recovers from both in the validated smoke path; file focused
  issues only if either produces a visible user failure.
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
