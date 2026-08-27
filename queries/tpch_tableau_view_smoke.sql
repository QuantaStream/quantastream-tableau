select
  market_segment,
  customer_region,
  ship_mode,
  count(*) as line_count,
  sum(extended_price) as gross_sales,
  avg(discount) as avg_discount
from tpch_order_line_sales_base
where ship_date between todate('1995-03-15') and todate('1998-11-30')
group by market_segment, customer_region, ship_mode
order by gross_sales desc
limit 25;

select
  order_key,
  sum(extended_price * (1 - discount)) as revenue,
  order_date,
  ship_priority
from q3_order_line_base
where market_segment = 'BUILDING'
  and order_date < todate('1995-03-15')
  and ship_date > todate('1995-03-15')
group by order_key, order_date, ship_priority
order by revenue desc, order_date
limit 10;
