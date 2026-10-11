"""Local medallion pipeline: immutable raw copy, validated rows, SQL analytics."""
import argparse
import csv
import hashlib
import html
import json
import shutil
import sqlite3
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIELDS = ['order_id', 'order_date', 'customer_id', 'region', 'product', 'quantity', 'unit_price']


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def clean(raw):
    """Keep first valid order ID; quarantine invalid or duplicate rows."""
    accepted, rejected, seen = [], [], set()
    for line, row in enumerate(raw, start=2):
        try:
            if None in row or any(row.get(k) is None for k in FIELDS):
                raise ValueError('incorrect column count')
            r = {k: row[k].strip() for k in FIELDS}
            if not all(r.values()):
                raise ValueError('missing required value')
            date.fromisoformat(r['order_date'])
            quantity = int(r['quantity'])
            price = Decimal(r['unit_price'])
            if quantity <= 0 or not price.is_finite() or price <= 0:
                raise ValueError('quantity and price must be positive finite values')
            if price != price.quantize(Decimal('0.01')):
                raise ValueError('price must have at most two decimal places')
            if r['order_id'] in seen:
                raise ValueError('duplicate order_id')
            seen.add(r['order_id'])
            r.update(region=r['region'].title(), product=r['product'].title(),
                     quantity=quantity, unit_price=f'{price:.2f}',
                     revenue=f'{quantity * price:.2f}')
            accepted.append(r)
        except (ValueError, InvalidOperation) as exc:
            rejected.append({'source_line': line, 'reason': str(exc), 'raw_row': json.dumps(row)})
    return accepted, rejected


def run(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    bronze = output / 'bronze' / 'orders.csv'
    if source == bronze:
        raise ValueError('source must be outside the Bronze destination')
    with source.open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != FIELDS:
            raise ValueError('CSV header must match: ' + ','.join(FIELDS))
        rows = list(reader)
    bronze.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, bronze)
    good, bad = clean(rows)
    write_csv(output / 'silver' / 'orders_clean.csv', good, FIELDS + ['revenue'])
    write_csv(output / 'silver' / 'rejected_rows.csv', bad, ['source_line', 'reason', 'raw_row'])
    with sqlite3.connect(output / 'warehouse.db') as db:
        db.execute('DROP TABLE IF EXISTS orders')
        db.execute('CREATE TABLE orders (order_id TEXT PRIMARY KEY, order_date TEXT, customer_id TEXT, region TEXT, product TEXT, quantity INTEGER, unit_price_cents INTEGER, revenue_cents INTEGER)')
        db.executemany('INSERT INTO orders VALUES (?,?,?,?,?,?,?,?)', [
            (r['order_id'], r['order_date'], r['customer_id'], r['region'], r['product'],
             r['quantity'], int(Decimal(r['unit_price']) * 100), int(Decimal(r['revenue']) * 100)) for r in good])
        queries = {
            'daily_sales': 'SELECT order_date, COUNT(*) AS orders, SUM(quantity) AS units, SUM(revenue_cents) AS revenue_cents FROM orders GROUP BY order_date ORDER BY order_date',
            'region_sales': 'SELECT region, COUNT(*) AS orders, SUM(revenue_cents) AS revenue_cents FROM orders GROUP BY region ORDER BY revenue_cents DESC, region',
            'product_sales': 'SELECT product, SUM(quantity) AS units, SUM(revenue_cents) AS revenue_cents FROM orders GROUP BY product ORDER BY revenue_cents DESC, product',
        }
        tables = {}
        for name, sql in queries.items():
            cursor = db.execute(sql)
            fields = [c[0] for c in cursor.description]
            result = [dict(zip(fields, row)) for row in cursor.fetchall()]
            tables[name] = result
            write_csv(output / 'gold' / (name + '.csv'), result, fields)
        total = db.execute('SELECT COALESCE(SUM(revenue_cents),0) FROM orders').fetchone()[0]
    report = {'input_rows': len(rows), 'accepted_rows': len(good), 'rejected_rows': len(bad),
              'total_revenue_cents': total, 'currency': 'INR',
              'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'execution_mode': 'local; no cloud services used'}
    (output / 'quality_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    cards = ''.join(f'<article><small>{label}</small><strong>{value}</strong></article>' for label, value in [
        ('Raw rows', len(rows)), ('Valid orders', len(good)), ('Quarantined', len(bad)), ('Revenue (INR)', f'{total / 100:,.2f}')])
    sections = ''
    for name, result in tables.items():
        fields = list(result[0]) if result else []
        header = ''.join('<th>' + html.escape(k.replace('_', ' ').title()) + '</th>' for k in fields)
        body = ''.join('<tr>' + ''.join('<td>' + html.escape(str(row[k])) + '</td>' for k in fields) + '</tr>' for row in result)
        sections += f'<section><h2>{name.replace("_", " ").title()}</h2><table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table></section>'
    dashboard = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Lakehouse sales analytics</title><style>
    body{font:16px system-ui;background:#edf2f7;color:#14283f;margin:0}main{max-width:1050px;margin:40px auto;padding:20px}h1{font-size:36px}p{color:#52677c}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:16px}article,section{background:white;padding:24px;border-radius:14px;margin-bottom:20px;overflow:auto}strong{display:block;font-size:28px;margin-top:12px}small{color:#52677c}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:12px;border-bottom:1px solid #e0e7ee}th{color:#276d8e}footer{padding:20px;color:#52677c}</style><main><p>DATA ENGINEERING / MEDALLION ARCHITECTURE</p><h1>Sales Lakehouse Analytics</h1><p>Local Python + SQLite pipeline using synthetic data. Revenue in tables is stored in integer paise (INR cents).</p><div class="cards">''' + cards + '</div>' + sections + '<footer>Bronze: raw data → Silver: validated data → Gold: business summaries</footer></main></html>'
    (output / 'dashboard.html').write_text(dashboard, encoding='utf-8')
    print(json.dumps(report, indent=2))
    print('Open dashboard:', output / 'dashboard.html')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT / 'data' / 'orders.csv')
    parser.add_argument('--output', type=Path, default=ROOT / 'output')
    args = parser.parse_args()
    run(args.input, args.output)
