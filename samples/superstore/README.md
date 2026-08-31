# Sample Superstore Data

Tableau's Sample Superstore is Tableau's common demo/training dataset. Use it
as the first compliance-oriented Tableau target for QuantaStream.

This repository does not vendor Tableau's original sample data. It provides a
compatible QuantaStream schema, a tiny synthetic Superstore-shaped CSV, and
loader scripts that can ingest either the synthetic file or your own exported
Sample Superstore Orders CSV.

Expected first target:

- an Orders worksheet or CSV with one row per order line;
- fields similar to Tableau's common Sample Superstore columns;
- dates parsed into ISO date values before loading into QuantaStream;
- money fields loaded as fixed-scale decimal values.

The first QuantaStream schema is `configuration/superstore_orders/schema.yaml`.
It models the Orders table as a single analytical fact table so Tableau can
exercise metadata, previews, filters, grouping, and aggregates without requiring
a connector-specific join model on day one.

## Quick Load

From the repository root, with the QuantaStream source checkout beside this
repository as `../quantastream`, run:

```bash
SAMPLE_CSV=/path/to/sample-superstore-orders.csv \
  BATCH_SIZE=1000 \
  scripts/run_local_superstore_loop.sh
```

To use the committed synthetic smoke file instead:

```bash
scripts/run_local_superstore_loop.sh
```

The loop starts QuantaStream, starts `qstream-loader`, loads
`superstore_orders`, and runs smoke queries. Then connect Tableau through
**Other Databases (JDBC)** and select the `superstore_orders` table.

## Loader Helpers

Two small scripts support local testing:

```bash
scripts/normalize_superstore_csv.py input.csv /tmp/superstore_orders_normalized.csv
scripts/load_superstore_csv.py -target http://127.0.0.1:8088/ingest/json input.csv
```

`load_superstore_csv.py` accepts either original Tableau Sample Superstore
headers or the normalized snake_case headers below. It posts JSON event batches
with `payload.type = "superstore_order"`, matching the schema selector.

## Suggested Normalized Column Names

The schema uses snake_case names that are stable for SQL and Tableau:

- `row_id`
- `order_id`
- `order_date`
- `ship_date`
- `ship_mode`
- `customer_id`
- `customer_name`
- `segment`
- `country_region`
- `city`
- `state_province`
- `postal_code`
- `region`
- `product_id`
- `category`
- `sub_category`
- `product_name`
- `sales`
- `quantity`
- `discount`
- `profit`

If the local Tableau sample uses slightly different names, normalize them during
CSV/JSON preparation rather than changing the SQL-facing test schema every time.

## Synthetic Smoke Data

samples/superstore/synthetic_orders.csv is a tiny QuantaStream-authored,
Superstore-shaped CSV. It is not Tableau sample data. Use it for deterministic
loader and query smoke checks before using Tableau's real Sample Superstore data.
