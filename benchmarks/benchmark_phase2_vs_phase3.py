"""benchmark_phase2_vs_phase3.py

Benchmarks Phase 2 baseline Treap vs Phase 3 optimized Treap.

Outputs:
- phase3_benchmark_results.csv
- phase3_insert.png
- phase3_search.png
- phase3_inorder_repeat.png
- phase3_delete.png

Run:
    python benchmark_phase2_vs_phase3.py
"""

from __future__ import annotations
import csv
import random
import time
import statistics
import matplotlib.pyplot as plt

from treap_phase2_baseline import InventoryTreap, InventoryItem as ItemV2
from treap_phase3_optimized import InventoryTreapOptimized, InventoryItem as ItemV3

DATASET = "./data/inventory_100k.csv"

def load_items(limit: int, seed: int = 42):
    """Load first 'limit' rows from DATASET."""
    items2, items3 = [], []
    with open(DATASET, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for i, row in enumerate(r):
            if i >= limit:
                break
            sku = row["sku"].strip()
            name = row["name"].strip()
            qty = int(row["quantity"])
            price = float(row["price"])
            items2.append(ItemV2(sku, name, qty, price))
            items3.append(ItemV3(sku, name, qty, price))
    return items2, items3

def time_once(fn):
    t0 = time.perf_counter()
    fn()
    return time.perf_counter() - t0

def time_mean(fn, reps=3):
    return statistics.mean(time_once(fn) for _ in range(reps))

def main():
    sizes = [1000, 2000, 5000, 10000, 20000, 50000, 100000]

    v2_insert, v3_insert = [], []
    v2_search, v3_search = [], []
    v2_inorder10, v3_inorder10 = [], []
    v2_delete, v3_delete = [], []

    for n in sizes:
        items2, items3 = load_items(n)

        # Build structures
        t2 = InventoryTreap(seed=42)
        t3 = InventoryTreapOptimized(seed=42, search_cache_size=20000)

        # Insert/bulk load
        v2_insert.append(time_once(lambda: [t2.insert(it) for it in items2]))
        v3_insert.append(time_once(lambda: t3.bulk_insert(items3)))

        # Search workload (5,000 random lookups)
        rng = random.Random(123)
        query_skus = [f"S{rng.randint(0, n-1):07d}" for _ in range(5000)]
        v2_search.append(time_mean(lambda: [t2.search(s) for s in query_skus], reps=3))
        v3_search.append(time_mean(lambda: [t3.search(s) for s in query_skus], reps=3))

        # Repeated inorder listing (10 calls)
        v2_inorder10.append(time_mean(lambda: [t2.inorder() for _ in range(10)], reps=3))
        v3_inorder10.append(time_mean(lambda: [t3.inorder() for _ in range(10)], reps=3))

        # Delete workload (delete 1,000 random SKUs where possible)
        del_count = 1000 if n >= 1000 else n
        del_skus = [f"S{rng.randint(0, n-1):07d}" for _ in range(del_count)]
        v2_delete.append(time_mean(lambda: [t2.delete(s) for s in del_skus], reps=3))
        v3_delete.append(time_mean(lambda: [t3.delete(s) for s in del_skus], reps=3))

    # Save results CSV
    with open("phase3_benchmark_results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["n","v2_insert_s","v3_insert_s","v2_search_5000_s","v3_search_5000_s",
                    "v2_inorder10_s","v3_inorder10_s","v2_delete1000_s","v3_delete1000_s"])
        for i, n in enumerate(sizes):
            w.writerow([n, v2_insert[i], v3_insert[i], v2_search[i], v3_search[i],
                        v2_inorder10[i], v3_inorder10[i], v2_delete[i], v3_delete[i]])

    # Plots
    def plot(xs, a, b, title, ylabel, outname):
        plt.figure()
        plt.plot(xs, a, marker="o", label="Phase 2 (baseline)")
        plt.plot(xs, b, marker="o", label="Phase 3 (optimized)")
        plt.xlabel("Number of items (n)")
        plt.ylabel(ylabel)
        plt.title(title)
        plt.legend()
        plt.tight_layout()
        plt.savefig(outname, dpi=160)

    plot(sizes, v2_insert, v3_insert, "Insert/Load Time vs Dataset Size", "Seconds", "phase3_insert.png")
    plot(sizes, v2_search, v3_search, "Search Time vs Dataset Size", "Seconds (5,000 lookups)", "phase3_search.png")
    plot(sizes, v2_inorder10, v3_inorder10, "Repeated Inorder Listing Time", "Seconds (10 inorder calls)", "phase3_inorder_repeat.png")
    plot(sizes, v2_delete, v3_delete, "Delete Time vs Dataset Size", "Seconds (1,000 deletes)", "phase3_delete.png")

    print("Wrote: phase3_benchmark_results.csv and 4 graphs")


if __name__ == "__main__":
    main()
