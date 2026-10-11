-- Run against output/warehouse.db with SQLite.
-- Monetary values are integer paise to avoid floating-point rounding.
SELECT region, COUNT(*) AS orders, SUM(revenue_cents) / 100.0 AS revenue_inr
FROM orders GROUP BY region ORDER BY revenue_inr DESC;

SELECT product, SUM(quantity) AS units, SUM(revenue_cents) / 100.0 AS revenue_inr
FROM orders GROUP BY product ORDER BY revenue_inr DESC;

SELECT order_date, SUM(revenue_cents) / 100.0 AS revenue_inr
FROM orders GROUP BY order_date ORDER BY order_date;
