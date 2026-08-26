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

A typical release-bundle flow is:

```bash
./bin/quantastream \
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
  -access-policy-file ./auth/access-policy.yaml
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
2. Choose the MySQL connector.
3. Use host `127.0.0.1`, port `4000`, database `quanta`.
4. Use the configured QuantaStream test user.
5. Select `superstore_orders`.
6. Preview rows.
7. Create a worksheet.

## First Worksheet Checks

Create these simple views:

- sales and profit by `region` and `category`;
- sales over `order_date` by month;
- profit by `segment` and `sub_category`;
- top products by `sales`;
- filters on `region`, `ship_mode`, and `order_date`.

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
