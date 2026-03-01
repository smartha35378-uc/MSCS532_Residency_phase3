# 🚀 Dynamic Inventory Management System

### Phase 3 -- Optimization, Scaling & Performance Evaluation

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Django](https://img.shields.io/badge/Django-4.x-green.svg) ![Data
Structure](https://img.shields.io/badge/Data%20Structure-Treap-orange.svg)
![Status](https://img.shields.io/badge/Status-Phase%203%20Complete-brightgreen.svg)
![License](https://img.shields.io/badge/License-Academic-lightgrey.svg)

------------------------------------------------------------------------

## 📌 Project Overview

This project implements a **Treap-based Dynamic Inventory Management
System** using Django.\
Phase 3 enhances the original proof-of-concept with optimization,
scalability testing, and performance benchmarking.

The system includes:

-   🌐 Web UI (Django templates)
-   💻 CLI (Django management command)
-   ⚡ Optimized Treap implementation
-   📊 Large dataset (100,000 items)
-   📈 Benchmark testing with performance graphs

------------------------------------------------------------------------

## 🔧 Phase 3 Optimizations

The following improvements were implemented:

-   ✅ Cached inorder traversal (dirty-flag pattern)
-   ✅ Iterative traversal (removed recursion overhead)
-   ✅ Bounded SKU search cache
-   ✅ Bulk dataset loading (`bulk_insert`)
-   ✅ Memory optimization using `@dataclass(slots=True)`
-   ✅ Environment-based dataset switching
-   ✅ Full benchmark comparison (Phase 2 vs Phase 3)

------------------------------------------------------------------------

## 🚀 Run the Web UI

``` bash
pip install django
python manage.py runserver
```

Open in browser:

    http://127.0.0.1:8000/

------------------------------------------------------------------------

## 💻 Run the CLI

``` bash
python manage.py inventory_cli
```

------------------------------------------------------------------------

## 📦 Use Large Dataset (100k rows)

Default dataset:

    data/inventory_dataset.csv

To use the 100k dataset without editing code:

``` bash
INVENTORY_DATASET=data/inventory_100k.csv python manage.py runserver
```

------------------------------------------------------------------------

## 📊 Run Benchmarks

``` bash
cd benchmarks
pip install matplotlib
python benchmark_phase2_vs_phase3.py
```

This generates:

-   `phase3_benchmark_results.csv`
-   Performance graphs:
    -   phase3_insert.png
    -   phase3_search.png
    -   phase3_inorder_repeat.png
    -   phase3_delete.png

------------------------------------------------------------------------

## 📁 Key Files (Phase 3)

-   `inventory/treap_ds_optimized.py` → Optimized Treap implementation
-   `inventory/services.py` → Uses optimized Treap + bulk insert
-   `inventory_site/settings.py` → Dataset configuration
-   `data/inventory_100k.csv` → Large dataset
-   `benchmarks/` → Performance testing tools

------------------------------------------------------------------------

## 🎯 Final Status

✔ Fully optimized Treap implementation\
✔ Scalable to 100,000+ records\
✔ Benchmarked with measured performance results\
✔ Web UI + CLI fully functional

------------------------------------------------------------------------

**Course Project -- Academic Use**
