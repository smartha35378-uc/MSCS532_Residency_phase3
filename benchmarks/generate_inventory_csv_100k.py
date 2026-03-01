"""generate_inventory_csv_100k.py

Generates a 100,000-row inventory dataset CSV for Phase 3 scaling tests.
The generated file is intended to be treated as READ-ONLY by the application.

Run:
    python generate_inventory_csv_100k.py --out inventory_100k.csv --n 100000
"""

import argparse
import csv
import random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="inventory_100k.csv")
    ap.add_argument("--n", type=int, default=100000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = random.Random(args.seed)

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sku", "name", "quantity", "price"])
        for i in range(args.n):
            sku = f"S{i:07d}"
            name = f"Item {i}"
            quantity = rng.randint(0, 500)
            price = round(rng.random() * 200, 2)
            w.writerow([sku, name, quantity, price])

    print(f"Wrote {args.n} rows to {args.out}")

if __name__ == "__main__":
    main()
