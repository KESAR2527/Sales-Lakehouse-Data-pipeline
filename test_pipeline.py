import csv
import tempfile
import unittest
from pathlib import Path
from pipeline import ROOT, clean, run


class PipelineTests(unittest.TestCase):
    def test_sample_totals_and_repeatability(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            first = run(ROOT / 'data/orders.csv', output)
            self.assertEqual((first['input_rows'], first['accepted_rows'], first['rejected_rows']), (20, 15, 5))
            self.assertEqual(first['total_revenue_cents'], 8700000)
            self.assertEqual((ROOT / 'data/orders.csv').read_bytes(), (output / 'bronze/orders.csv').read_bytes())
            with (output / 'gold/region_sales.csv').open() as f:
                regions = list(csv.DictReader(f))
            self.assertEqual(sum(int(r['revenue_cents']) for r in regions), first['total_revenue_cents'])
            self.assertEqual(run(ROOT / 'data/orders.csv', output), first)

    def test_invalid_prices_and_duplicate_policy(self):
        row = dict(order_id='1', order_date='2026-10-01', customer_id='C1', region=' south ', product='mouse', quantity='1', unit_price='1.20')
        good, bad = clean([dict(row, unit_price='NaN'), row, row, dict(row, order_id='2', unit_price='1.234')])
        self.assertEqual(len(good), 1)
        self.assertEqual(len(bad), 3)
        self.assertEqual(good[0]['region'], 'South')
        self.assertEqual(good[0]['revenue'], '1.20')

    def test_empty_input(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'empty.csv'
            path.write_text('order_id,order_date,customer_id,region,product,quantity,unit_price\n')
            result = run(path, Path(folder) / 'out')
            self.assertEqual(result['total_revenue_cents'], 0)
            self.assertEqual(result['accepted_rows'], 0)


if __name__ == '__main__':
    unittest.main()
