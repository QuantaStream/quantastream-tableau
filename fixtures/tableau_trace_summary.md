# MySQL Command Trace Summary

Events: 7
Unique SQL statements: 7

## Command Kind

| Value | Count |
| --- | ---: |
| `query` | 7 |

## Response

| Value | Count |
| --- | ---: |
| `error` | 1 |
| `ok` | 1 |
| `query` | 5 |

## Errors

| Value | Count |
| --- | ---: |
| `parser_boundary` | 1 |

## Top SQL

| Count | SQL |
| ---: | --- |
| 1 | `set names utf8mb4` |
| 1 | `select @@version as version_value, @@version_comment as version_comment` |
| 1 | `show full tables` |
| 1 | `select region, sum(sales) as sales from superstore_orders group by region order by sales desc limit 10` |
| 1 | `select * from ( select region, category, sales from superstore_orders ) TableauSQL where TableauSQL.sales > 0 limit 10` |
| 1 | `select count(*) as row_count from ( select order_id from superstore_orders ) TableauExtract` |
| 1 | `select unsupported_over()` |
