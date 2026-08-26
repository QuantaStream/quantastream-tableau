-- QuantaStream/Tableau Superstore smoke queries.
-- These query shapes mirror the first Tableau Desktop worksheet checks.

select count(*) as superstore_orders_count from superstore_orders;

select
  region,
  category,
  sum(sales) as sales,
  sum(profit) as profit
from superstore_orders
group by region, category
order by sales desc
limit 20;

select
  segment,
  sub_category,
  count(*) as orders,
  sum(sales) as sales,
  avg(discount) as avg_discount
from superstore_orders
group by segment, sub_category
order by sales desc
limit 20;

select
  order_date,
  region,
  sum(sales) as sales,
  sum(profit) as profit
from superstore_orders
where order_date >= '2026-01-01'
  and order_date < '2026-04-01'
group by order_date, region
order by order_date, region
limit 50;

select
  product_name,
  category,
  sub_category,
  sum(sales) as sales,
  sum(profit) as profit
from superstore_orders
group by product_name, category, sub_category
order by sales desc
limit 20;

select
  ship_mode,
  count(*) as orders,
  sum(quantity) as quantity,
  sum(sales) as sales
from superstore_orders
where region in ('East', 'West')
group by ship_mode
order by orders desc, ship_mode
limit 20;
