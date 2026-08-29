# TPC-H Tableau Views

Tableau Desktop works against QuantaStream through **Other Databases (JDBC)**
with the MySQL Connector/J driver. Manual relationships work in this path, but
current Tableau Desktop traces show the generic JDBC connector reading table and
primary-key metadata without requesting foreign-key discovery metadata during
the relationship drag/drop flow.

For relationship-heavy models, curated views are the smoother Tableau package:
they make joins explicit, keep worksheets focused on business fields, and avoid
asking every user to reconstruct the same relationship graph.

This is also the current best answer for dimensions that Tableau would otherwise
join to a view. Tableau can emit `LEFT JOIN` SQL for a relationship from a view
to another table, and QuantaStream's relationship-vector execution currently
supports only the inner-join slice in that path. Package those fields inside the
view instead.

Including useful dimensions inside a curated view is not expected to create a
meaningful steady-state penalty when a worksheet does not use those dimensions.
QuantaStream prunes unused projected fields, and local TPC-H `.05` smoke checks
showed the wider product-enriched view performing in the same range as the
smaller no-product view for queries grouped only by customer region and market
segment. Full join elimination is still future optimizer polish, but the
packaged-view approach is practical today.

## Included Views

- `q3_order_line_base`: the compact TPC-H Q3 shape over `customer`, `orders`,
  and `lineitem`.
- `tpch_order_line_sales_base`: a wider Tableau-oriented order-line view that
  adds customer nation, customer region, product dimensions, and commonly useful
  order and lineitem fields.

The canonical install script is:

```bash
mysql -h 127.0.0.1 -P 4000 -u qstream -D quanta \
  < /path/to/quantastream-tableau/queries/tpch_tableau_views.sql
```

Verify that QuantaStream registered the views:

```bash
mysql -h 127.0.0.1 -P 4000 -u qstream -D quanta \
  -e 'show full tables;'
```

Run the smoke queries:

```bash
mysql -h 127.0.0.1 -P 4000 -u qstream -D quanta \
  < /path/to/quantastream-tableau/queries/tpch_tableau_view_smoke.sql
```

## Tableau Flow

1. Connect with **Other Databases (JDBC)**.
2. Use a MySQL JDBC URL such as:

   ```text
   jdbc:mysql://127.0.0.1:4000/quanta?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC
   ```

   When Tableau Desktop runs on Windows and QuantaStream runs inside WSL:

   ```text
   jdbc:mysql://wsl.localhost:4000/quanta?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC
   ```

3. Select the `quanta` database.
4. Use `tpch_order_line_sales_base` as the worksheet source.
5. Build worksheets such as:

- gross sales by `customer_region`, `market_segment`, and `ship_mode`;
- gross sales by `part_type` or `part_brand`;
- line count by `order_date`;
- average discount by `customer_nation` and `ship_mode`;
- Q3-style revenue from `q3_order_line_base`.

The YAML files under `configuration/views/` mirror the SQL definitions for
inspection and package review. Installing through SQL is preferred because it
lets QuantaStream write the runtime view catalog entries.
