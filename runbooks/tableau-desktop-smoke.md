# Tableau Desktop Smoke Runbook

This runbook is the first manual Tableau compatibility loop. It assumes Tableau
Desktop is installed locally and QuantaStream is already running.

## Start QuantaStream

Use a local QuantaStream server with the MySQL endpoint on port `4000` and the
`superstore_orders` schema deployed.

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

## Verify With The MySQL CLI

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

## Connect Tableau Desktop

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
