drop view if exists q3_order_line_base;

create or replace view q3_order_line_base as
select
  c.c_mktsegment as market_segment,
  o.o_orderkey as order_key,
  o.o_orderdate as order_date,
  o.o_shippriority as ship_priority,
  l.l_extendedprice as extended_price,
  l.l_discount as discount,
  l.l_shipdate as ship_date
from customer as c
inner join orders as o on c.c_custkey = o.o_custkey
inner join lineitem as l on o.o_orderkey = l.l_orderkey;

drop view if exists tpch_order_line_sales_base;

create or replace view tpch_order_line_sales_base as
select
  c.c_custkey as customer_key,
  c.c_name as customer_name,
  c.c_mktsegment as market_segment,
  n.n_name as customer_nation,
  r.r_name as customer_region,
  o.o_orderkey as order_key,
  o.o_orderstatus as order_status,
  o.o_orderdate as order_date,
  o.o_orderpriority as order_priority,
  o.o_shippriority as ship_priority,
  l.l_linenumber as line_number,
  l.l_partkey as part_key,
  l.l_suppkey as supplier_key,
  l.l_quantity as quantity,
  l.l_extendedprice as extended_price,
  l.l_discount as discount,
  l.l_tax as tax,
  l.l_returnflag as return_flag,
  l.l_linestatus as line_status,
  l.l_shipdate as ship_date,
  l.l_commitdate as commit_date,
  l.l_receiptdate as receipt_date,
  l.l_shipmode as ship_mode
from customer as c
inner join orders as o on c.c_custkey = o.o_custkey
inner join lineitem as l on o.o_orderkey = l.l_orderkey
inner join nation as n on c.c_nationkey = n.n_nationkey
inner join region as r on n.n_regionkey = r.r_regionkey;
