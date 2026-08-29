# Tableau Compatibility Plan

This plan defines the first QuantaStream/Tableau integration path. The first
path is Tableau Desktop using **Other Databases (JDBC)** with the MySQL JDBC
driver against the QuantaStream MySQL-compatible endpoint.

A dedicated Tableau connector, TDVT verification, and Tableau Exchange packaging
are later distribution questions. The immediate goal is to make the default
Tableau connection boring: connect, browse, preview, manually define
relationships where needed, build worksheets, and capture any generated SQL
that QuantaStream does not yet support.

## Milestone 1: JDBC Connector Smoke

Goal: Tableau Desktop connects to a local QuantaStream server and opens a data
source page without client errors.

Expected setup:

- QuantaStream single-node server running on `127.0.0.1:4000`.
- Static or permissive QS auth configured for a local test user.
- `superstore_orders` deployed and loaded with Tableau Sample Superstore data.
- MySQL command tracing enabled with `QUANTASTREAM_MYSQL_COMMAND_TRACE=true`.

Smoke actions:

1. Connect with Tableau's **Other Databases (JDBC)** connector and the MySQL
   Connector/J driver.
2. Select the `quanta` database.
3. Confirm Tableau can list tables.
4. Drag `superstore_orders` onto the data source canvas.
5. Preview rows.
6. Build a worksheet with `Region`, `Category`, `Sales`, and `Profit`.
7. Add filters on `Order Date`, `Segment`, and `Sub-Category`.
8. Record any SQL errors and generated statements.

Exit criteria:

- Tableau connects without startup errors.
- Tableau shows `superstore_orders` fields with reasonable types.
- A simple aggregate worksheet returns data.
- Captured generated SQL is either supported or documented as a known gap.

## Milestone 2: Metadata Replay Suite

Goal: convert Tableau connection and schema-browsing SQL into repeatable tests.

Capture with `scripts/summarize_mysql_trace.py`, generate classified draft
replay suites with `scripts/trace_to_sqlrunner.py --classify` or
`--split-by-phase`, then review:

- session setup, including `SET`, `USE`, `SELECT @@...`, and version probes;
- database and table discovery;
- column metadata;
- table status and index metadata;
- preview query shapes;
- unsupported queries that should return a client-friendly error.

Target deliverables in the QuantaStream engine repo:

- `sqlrunner/sqltests/mysql_compat_tableau_connect.yaml` captures startup
  session setup, version probes, connection metadata functions, charset probes,
  database selection, warning reads, and ping queries.
- `sqlrunner/sqltests/mysql_compat_tableau_metadata.yaml` captures session,
  variable, database, table, column, index, preview, and explain probes.
- `sqlrunner/sqltests/mysql_compat_tableau_superstore_metadata.yaml` captures
  the same catalog, table, column, index, preview, and explain probes against
  the Tableau Sample Superstore-style schema.
- `sqlrunner/sqltests/mysql_compat_tableau_superstore_worksheets.yaml` captures
  live worksheet query shapes over the Tableau Sample Superstore-style schema.
- `sqlrunner/sqltests/mysql_compat_tableau_worksheets.yaml` captures common
  live worksheet query shapes over the TPC-H schema.
- `sqlrunner/sqltests/mysql_compat_tableau_custom_sql.yaml` captures Tableau's
  custom-SQL wrapper pattern around derived tables.
- `sqlrunner/sqltests/mysql_compat_tableau_extract.yaml` captures bounded
  extract-style count, scan, incremental-refresh, and join probes.

Run the current replay set from this repository with:

```bash
scripts/run_engine_tableau_suites.sh
```

By default the helper uses `ENGINE=inabox-standard`, expects the engine repo
at `../quantastream`, and targets a local QS MySQL-compatible endpoint on
`127.0.0.1:4000` with `superstore_orders` loaded. Set `TABLEAU_SUITES` to run
the broader TPC-H, custom SQL, or extract suites. Set `ENGINE=inabox-direct` and
`CONSUL_ADDR=127.0.0.1:8500` for direct cluster testing, or set
`ENGINE=mysql-reference` with `MYSQL_DSN` for reference checks where the target
suite is compatible with the MySQL fixture.

This repository should keep sanitized capture notes in `captures/` and use new
captures to refine the curated engine replay suites.

## Milestone 3: Worksheet Query Coverage

Goal: Tableau can generate useful live worksheets against Superstore.

Priority query shapes:

- `SELECT * ... LIMIT n` previews;
- explicit projection lists with aliases;
- table aliases;
- equality, range, `IN`, `IS NULL`, and `IS NOT NULL` filters;
- date filters over `order_date` and `ship_date`;
- grouped `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`;
- `COUNT(DISTINCT ...)` where Tableau emits it;
- `ORDER BY` aggregate alias or expression;
- `LIMIT` and `OFFSET`;
- common scalar functions Tableau emits for calculated fields.

Exit criteria:

- A worksheet can group sales and profit by region/category/sub-category.
- Date filters work over order and ship dates.
- Top-N style worksheets either work directly or have a documented supported
  expression path.

## Relationship Behavior

Manual Tableau relationships are supported in the current preview. A TPC-H smoke
can manually relate `customer` to `orders` on
`customer.c_custkey = orders.o_custkey`, and `orders` to `lineitem` on
`orders.o_orderkey = lineitem.l_orderkey`, then build worksheets across all
three tables.

Automatic relationship inference is not a first-preview requirement. Current
Tableau Desktop traces show the generic JDBC path reading table metadata and
primary keys, then opening Tableau's relationship editor without requesting
foreign-key discovery metadata from QuantaStream. A dedicated Tableau connector
package may be the right place to improve this later.

For release packaging and public demos, curated views are the preferred path for
relationship-heavy datasets. The Tableau package now includes
`queries/tpch_tableau_views.sql` plus matching YAML view definitions under
`configuration/views/`. These install `q3_order_line_base` and
`tpch_order_line_sales_base`, giving Tableau users a worksheet-ready TPC-H
source with customer, order, lineitem, region, and product fields without
relying on JDBC relationship auto-discovery.

One current engine limitation is worth keeping explicit: Tableau relationships
from a curated view to another physical table can produce `LEFT JOIN` SQL, for
example `tpch_order_line_sales_base LEFT JOIN part`. QuantaStream currently
rejects that path with
`relationship-vector graph execution only supports inner relationship-vector
joins in this slice`. Until left joins are supported for this execution path,
the preferred packaging approach is to include the required dimensions directly
inside the curated view.

That packaging choice is also reasonable from a performance perspective.
QuantaStream prunes unused projected fields from the view expansion, and local
TPC-H `.05` smoke checks showed no meaningful steady-state penalty when the
view included product dimensions but the worksheet queried only customer region,
market segment, and extended price. Join elimination for unused
cardinality-preserving view joins remains useful future optimizer polish, but it
is not required for the current Tableau packaging approach.

## Current Engine Replay Suites

The curated engine suites currently cover:

- connection startup/session setup;
- metadata/session/catalog discovery;
- preview and worksheet-style SQL;
- Tableau custom SQL wrappers over derived tables;
- bounded extract-style count, scan, incremental refresh, and join probes.

They are intentionally TPC-H based today because the engine repo already has a
stable TPC-H fixture path. Superstore-specific replay can be added after actual
Tableau Desktop captures show the generated SQL shapes.

## Milestone 4: Custom SQL And Extract Smoke

Goal: prove the important Tableau power-user paths without broadening scope too
far.

Custom SQL:

- capture Tableau's wrapper shape around custom SQL;
- support the common `select * from (<custom query>) TableauSQL ...` form;
- return clear errors for unsupported nested or window-function-heavy SQL.

Extract smoke:

- engine replay now covers bounded extract-style probes in
  `mysql_compat_tableau_extract.yaml`;
- create a small extract from `superstore_orders` or a curated demo view in
  Tableau Desktop;
- capture real extract SQL and compare it to the bounded replay suite;
- measure proxy memory and cancellation behavior;
- document any first-release extract size guidance.

Current result:

- Tableau Desktop extract creation was validated through **Other Databases
  (JDBC)** against a radiosport contest view.
- The engine-side compatibility requirements identified by that pass are
  `NOW()`/`CURRENT_TIMESTAMP()` scalar projection support and explicit UTC
  server time-zone metadata: `@@system_time_zone=UTC` and `@@time_zone=+00:00`.
- The validated trace shows Connector/J startup, metadata browsing, extract
  scan/count queries, and worksheet queries returning successfully.
- Non-blocking Tableau probes remain visible in traces: a synthetic one-column
  `GROUP BY 2` capability check and `SHOW KEYS` against a view. Tableau
  recovered from both in the smoke path, so they should become focused issues
  only if they cause visible client failures.

## Later Work

Later work can include:

- Tableau Datasource Verification Tool runs;
- a dedicated Tableau connector package if the generic JDBC path needs richer
  metadata behavior, automatic relationship hints, or Tableau Exchange
  packaging;
- Tableau Public dashboards built from exported QuantaStream snapshots;
- radiosport demo workbooks that show QuantaStream's streaming and
  bitmap-native strengths.
