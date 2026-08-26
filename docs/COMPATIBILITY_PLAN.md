# Tableau Compatibility Plan

This plan defines the first QuantaStream/Tableau integration path. The first
path is Tableau Desktop using Tableau's built-in MySQL connector against the
QuantaStream MySQL-compatible endpoint.

A dedicated Tableau connector, TDVT verification, and Tableau Exchange packaging
are later distribution questions. The immediate goal is to make the default
Tableau connection boring: connect, browse, preview, build worksheets, and
capture any generated SQL that QuantaStream does not yet support.

## Milestone 1: Native MySQL Connector Smoke

Goal: Tableau Desktop connects to a local QuantaStream server and opens a data
source page without client errors.

Expected setup:

- QuantaStream single-node server running on `127.0.0.1:4000`.
- Static or permissive QS auth configured for a local test user.
- `superstore_orders` deployed and loaded with Tableau Sample Superstore data.
- MySQL command tracing enabled with `QUANTASTREAM_MYSQL_COMMAND_TRACE=true`.

Smoke actions:

1. Connect with Tableau's MySQL connector.
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

Capture with `scripts/summarize_mysql_trace.py`, generate a draft replay suite
with `scripts/trace_to_sqlrunner.py`, then classify:

- session setup, including `SET`, `USE`, `SELECT @@...`, and version probes;
- database and table discovery;
- column metadata;
- table status and index metadata;
- preview query shapes;
- unsupported queries that should return a client-friendly error.

Target deliverables in the QuantaStream engine repo:

- `sqlrunner/sqltests/mysql_compat_tableau_connect.yaml`
- `sqlrunner/sqltests/mysql_compat_tableau_metadata.yaml`
- `sqlrunner/sqltests/mysql_compat_tableau_worksheets.yaml`

This repository should keep sanitized capture notes in `captures/` and link to
the engine replay suites once they exist.

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

## Milestone 4: Custom SQL And Extract Smoke

Goal: prove the important Tableau power-user paths without broadening scope too
far.

Custom SQL:

- capture Tableau's wrapper shape around custom SQL;
- support the common `select * from (<custom query>) TableauSQL ...` form;
- return clear errors for unsupported nested or window-function-heavy SQL.

Extract smoke:

- create a small extract from `superstore_orders`;
- capture extract SQL;
- measure proxy memory and cancellation behavior;
- document any first-release extract size guidance.

## Later Work

Later work can include:

- Tableau Datasource Verification Tool runs;
- a dedicated Tableau connector package if the native MySQL path is not enough;
- Tableau Public dashboards built from exported QuantaStream snapshots;
- radiosport demo workbooks that show QuantaStream's streaming and
  bitmap-native strengths.
