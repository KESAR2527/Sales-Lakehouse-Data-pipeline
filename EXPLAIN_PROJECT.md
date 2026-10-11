# Understand the project in five minutes

## What does it do?

It takes a messy list of shop orders and turns it into trustworthy sales summaries.

1. **Bronze = original data.** The program copies the source CSV exactly so the original records can be inspected.
2. **Silver = cleaned data.** It fixes extra spaces and capitalization, checks dates, rejects missing fields and invalid amounts, and removes repeated order IDs. Rejected records are saved with a reason.
3. **Warehouse = queryable records.** Clean orders are inserted into SQLite, a database stored in one file.
4. **Gold = useful answers.** SQL groups orders to calculate sales by day, region and product.
5. **Dashboard = readable output.** The generated HTML shows totals and tables. Double-click it to view the results.

## One order example

The first order has region ` south `, quantity `2` and unit price `1500.00`. The program changes the region to `South` and calculates revenue as `2 × 1500 = ₹3,000`. Its database revenue is stored as `300000` paise.

## Why are five rows rejected?

There is one repeated order ID, one negative quantity, one text value in the price field, one missing customer ID and one impossible date. Read `output/silver/rejected_rows.csv` to see them.

## Where to look in the code

- `write_csv()` saves a table as a CSV file.
- `clean()` checks each row and puts it in the accepted or rejected list.
- `run()` copies raw data, calls cleaning, loads SQLite, runs SQL and writes outputs.
- The final block reads command-line options and starts the pipeline.

## An accurate explanation you can adapt

“This is a local sales data engineering project using Python and SQLite. I use three layers: Bronze preserves raw data, Silver validates and cleans orders, and Gold summarizes sales using SQL. The sample contains 20 rows, of which 15 are valid and five are rejected. A generated dashboard shows total revenue and sales breakdowns. The architecture could be extended to cloud services, but this implementation runs locally. I used AI assistance to create the starter project.”

Use “I ran and checked the pipeline” only after doing that yourself. Describe modifications only after actually making them.

## Small exercises to make it yours

1. Add a valid order with a NEW order ID to `data/orders.csv`, then rerun. Predict the revenue change first.
2. Add an order with quantity zero and inspect its rejection reason.
3. Read `sql/analytics.sql`: `GROUP BY region` combines orders from the same region, and `SUM(revenue_cents)` adds their revenue.
4. Run twice and observe that orders are replaced rather than doubled.

## Questions you should be able to answer

**Is it deployed on AWS?** No. It is a local implementation with a proposed cloud extension.

**Why preserve Bronze?** To retain the original input for auditing and troubleshooting.

**Why separate rejected rows?** To keep bad data out of analytics while preserving enough information to fix it.

**How is revenue calculated?** Quantity multiplied by unit price for every accepted order, then summed.

**Why SQLite?** It runs without a database server and makes this small project easy to reproduce.
