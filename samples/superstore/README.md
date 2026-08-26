# Sample Superstore Data

Use Tableau's Sample Superstore data as the first compliance-oriented Tableau
target. This repository does not vendor Tableau sample data. Place a local copy
here only for private/manual testing, or point loader scripts at the downloaded
file path.

Expected first target:

- an Orders worksheet or CSV with one row per order line;
- fields similar to Tableau's common Sample Superstore columns;
- dates parsed into ISO date values before loading into QuantaStream;
- money fields loaded as fixed-scale decimal values.

The first QuantaStream schema is `configuration/superstore_orders/schema.yaml`.
It models the Orders table as a single analytical fact table so Tableau can
exercise metadata, previews, filters, grouping, and aggregates without requiring
a connector-specific join model on day one.

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
