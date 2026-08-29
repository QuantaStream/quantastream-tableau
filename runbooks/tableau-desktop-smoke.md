# Tableau Desktop Smoke Runbook

This runbook is the first manual Tableau compatibility loop. It assumes Tableau
Desktop is installed locally and QuantaStream is already running or available as
a release bundle.

## 1. Stage The Superstore Schema

From a QuantaStream release bundle directory, copy the Superstore schema into
the runtime configuration directory:

```bash
cp -R /path/to/quantastream-tableau/configuration/superstore_orders \
  ./runtime/config/
```

Deploy it into the local catalog:

```bash
./bin/qstream-admin create --schema-dir=./runtime/config superstore_orders
```

When working from the QuantaStream source tree, use the source admin command
instead:

```bash
go run ./quanta-admin create \
  --schema-dir=/path/to/quantastream-tableau/configuration \
  superstore_orders
```

## 2. Start QuantaStream

Use a local QuantaStream server with the MySQL endpoint on port `4000` and the
native gRPC endpoint on port `4100`.

A typical release-bundle flow is below. Keep command tracing enabled while
capturing Tableau-generated SQL.

```bash
QUANTASTREAM_MYSQL_COMMAND_TRACE=true ./bin/quantastream \
  -config-dir ./runtime/config \
  -data-dir ./data \
  -wal-path ./data/storage.wal \
  -bind 127.0.0.1 \
  -mysql-port 4000 \
  -native-grpc-bind 127.0.0.1 \
  -native-grpc-port 4100 \
  -database quanta \
  -auth-mode static \
  -auth-account-file ./auth/accounts.yaml \
  -access-policy-file ./auth/access-policy.yaml \
  2>&1 | tee /tmp/quantastream-tableau.log
```

## 3. Start The JSON Loader

In a second terminal:

```bash
./bin/qstream-loader \
  -connection-mode standard-native \
  -native-grpc-addr 127.0.0.1:4100 \
  -config-dir ./runtime/config \
  -tables superstore_orders \
  -listen 127.0.0.1:8088 \
  -workers 4 \
  -channel-size 100000 \
  -flush-interval 500ms
```

Verify the loader is ready:

```bash
curl -fsS http://127.0.0.1:8088/healthz
```

Expected shape:

```json
{"connection_mode":"standard-native","status":"ok","tables":1}
```

## 4. Prepare Sample Superstore CSV

This repository does not vendor Tableau sample data. Export or download the
Tableau Sample Superstore Orders CSV, then normalize it if desired:

```bash
/path/to/quantastream-tableau/scripts/normalize_superstore_csv.py \
  /path/to/Sample-Superstore-Orders.csv \
  /tmp/superstore_orders_normalized.csv
```

The loader script also accepts the original Tableau headers directly, so this
normalization step is optional. It is useful for inspection and repeatability.

## 5. Load Superstore Into QuantaStream

```bash
/path/to/quantastream-tableau/scripts/load_superstore_csv.py \
  -target http://127.0.0.1:8088/ingest/json \
  -batch-size 1000 \
  -workers 4 \
  /path/to/Sample-Superstore-Orders.csv
```

Check loader stats:

```bash
curl -fsS http://127.0.0.1:8088/stats | python3 -m json.tool | head -80
```

## 6. Verify With The MySQL CLI

```bash
mysql -h 127.0.0.1 -P 4000 -u qstream -D quanta \
  -e 'select count(*) from superstore_orders;'
```

Then run a worksheet-like query:

```sql
select
  region,
  category,
  sum(sales) as sales,
  sum(profit) as profit
from superstore_orders
group by region, category
order by sales desc
limit 20;
```

## 7. Connect Tableau Desktop

1. Open Tableau Desktop.
2. Choose **Other Databases (JDBC)**.
3. Use the MySQL Connector/J driver.

   The current smoke path was tested with Oracle MySQL Connector/J `8.4.0`.
   Tableau did not ship this jar in the tested Windows install; it was
   downloaded separately and placed under:

   ```text
   C:\Program Files\Tableau\Drivers\mysql-connector-j-8.4.0.jar
   ```

   A compatibility-named copy was also present as:

   ```text
   C:\Program Files\Tableau\Drivers\mysql-connector-java-8.4.0.jar
   ```

   Both files had the same SHA-256 hash:

   ```text
   D77962877D010777CFF997015DA90EE689F0F4BB76848340E1488F2B83332AF5
   ```

   Restart Tableau Desktop after adding or replacing the driver jar.
4. Use a JDBC URL:

   ```text
   jdbc:mysql://127.0.0.1:4000/quanta?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC
   ```

   When Tableau Desktop runs on Windows and QuantaStream runs inside WSL, use:

   ```text
   jdbc:mysql://wsl.localhost:4000/quanta?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC
   ```

5. Use the configured QuantaStream test user, for example `qstream`.
6. Select the `quanta` database.
7. Select `superstore_orders`.
8. Preview rows.
9. Create a worksheet.

Do not use Tableau's built-in MySQL connector for this preview path. It may
route users back through Tableau's MySQL-driver installation flow, while the
generic JDBC path is the route currently exercised by the QuantaStream Tableau
compatibility suites.

## First Worksheet Checks

Create these simple views:

- sales and profit by `region` and `category`;
- sales over `order_date` by month;
- profit by `segment` and `sub_category`;
- top products by `sales`;
- filters on `region`, `ship_mode`, and `order_date`.

## Extract Smoke

After the live worksheet path works, switch the Tableau data source from live
mode to extract mode and create a small extract. The validated path uses the
generic JDBC connector, MySQL Connector/J, and a JDBC URL with
`serverTimezone=UTC`.

Expected QS behavior:

- Connector/J startup metadata returns successfully.
- `SELECT NOW()` returns successfully.
- `@@system_time_zone` reports `UTC`.
- `@@time_zone` reports `+00:00`.
- Tableau can run extract scan/count queries and build a worksheet from the
  extract without a time-zone warning.

If Tableau reports that the extract has a different time zone from the
underlying server, confirm the QuantaStream engine includes the SQL
`NOW()`/`CURRENT_TIMESTAMP()` and explicit UTC time-zone metadata fixes.

The QS command trace may still show these non-blocking Tableau probes:

- `SELECT SUBCOL AS COL FROM (SELECT 1 AS SUBCOL) SUBQUERY GROUP BY 2`
  returning `GROUP BY ordinal is out of range`;
- `SHOW KEYS FROM <view> FROM <schema>` returning view/index metadata as a
  missing physical table.

Those probes did not block the validated extract smoke. Treat them as new
issues only if Tableau surfaces a visible failure.

## Relationship Checks

Manual Tableau relationships work with QuantaStream today. Automatic
relationship inference is not expected in the current preview. Tableau's
generic JDBC path reads columns and primary keys from QuantaStream, then opens
the relationship editor without requesting foreign-key discovery metadata.

For a TPC-H relationship smoke, drag these tables onto the Tableau data source
canvas and define the relationships manually:

- `customer.c_custkey = orders.o_custkey`
- `orders.o_orderkey = lineitem.l_orderkey`

Then build a simple worksheet across the three tables, such as order date by
customer segment with lineitem count or extended price sum.

For packaged demos or first-user walkthroughs, curated views are usually better
than manual relationships. Install the TPC-H view package from this repository:

```bash
mysql -h 127.0.0.1 -P 4000 -u qstream -D quanta \
  < /path/to/quantastream-tableau/queries/tpch_tableau_views.sql
```

Then use `tpch_order_line_sales_base` directly in Tableau. It flattens the
`customer -> orders -> lineitem -> part -> nation -> region` path into
worksheet-ready fields while keeping the underlying QuantaStream schema
normalized.

Avoid adding another physical table as a Tableau relationship from this curated
view for now. Tableau may emit a `LEFT JOIN` from the view to that table, and
QuantaStream currently supports only the inner relationship-vector join slice in
that execution path. If a worksheet needs another dimension, add it to the
curated view package first.

## Capture Template

For each failure, capture:

- Tableau version;
- QuantaStream version;
- OS;
- action that triggered the query;
- full SQL text if available;
- QS log excerpt;
- client error text;
- whether the same SQL works in `mysql` CLI.

Store sanitized notes under `captures/`.

## QS Trace And Support Bundle

Keep QS command tracing enabled while reproducing Tableau issues:

```bash
QUANTASTREAM_MYSQL_COMMAND_TRACE=true ./bin/quantastream \
  -config-dir ./runtime/config \
  -data-dir ./data \
  -wal-path ./data/storage.wal \
  -bind 127.0.0.1 \
  -mysql-port 4000 \
  -native-grpc-bind 127.0.0.1 \
  -native-grpc-port 4100 \
  -database quanta \
  -auth-mode static \
  -auth-account-file ./auth/accounts.yaml \
  -access-policy-file ./auth/access-policy.yaml \
  2>&1 | tee /tmp/quantastream-tableau.log
```

Create a QuantaStream support bundle and include the trace log as a log tail:

```bash
./bin/qstream-admin support bundle \
  --output /tmp/qstream-tableau-support-$(date -u +%Y%m%dT%H%M%SZ).tar.gz \
  --data-dir ./data \
  --config-dir ./runtime/config \
  --wal-path ./data/storage.wal \
  --auth-account-file ./auth/accounts.yaml \
  --access-policy-file ./auth/access-policy.yaml \
  --log-path /tmp/quantastream-tableau.log
```

From a source checkout, replace `./bin/qstream-admin` with
`go run ./quanta-admin` from the QuantaStream repository. The support bundle
does not include table data files or raw auth/access files. Review any included
log tails for local paths, credentials, or private data before sharing.

Tableau Desktop logs are separate from the QS support bundle. On Windows they
are usually under `Documents/My Tableau Repository/Logs`; localized installs may
translate the directory names. Include a short sanitized excerpt only when the
QS trace does not explain the issue.

## Summarize The QS Command Trace

After the Tableau session, convert the QS trace log into a compact inventory:

```bash
/path/to/quantastream-tableau/scripts/summarize_mysql_trace.py \
  /tmp/quantastream-tableau.log \
  > /path/to/quantastream-tableau/captures/tableau-desktop-smoke-summary.md

/path/to/quantastream-tableau/scripts/summarize_mysql_trace.py \
  /tmp/quantastream-tableau.log \
  --format json \
  --events-jsonl /path/to/quantastream-tableau/captures/tableau-desktop-smoke-events.jsonl \
  > /path/to/quantastream-tableau/captures/tableau-desktop-smoke-summary.json
```

The Markdown summary is meant for human triage. The JSON/JSONL output is useful
when converting captured SQL into SQLRunner replay suites.

Generate a first-pass replay suite:

```bash
/path/to/quantastream-tableau/scripts/trace_to_sqlrunner.py \
  /tmp/quantastream-tableau.log \
  > /path/to/quantastream-tableau/captures/sqlrunner/mysql_compat_tableau_capture.yaml
```

Use `--include-errors` when you want failed Tableau-generated SQL emitted as
`xfail` cases for compatibility triage. Review generated suites before moving
them into `quantastream/sqlrunner/sqltests`.
