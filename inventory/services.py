"""inventory.services (Phase 3)

Uses the optimized Treap implementation for better performance at scale.
- Inorder cache + dirty flag
- Iterative traversal
- Bounded search cache
- Bulk insert for dataset loads

Dataset handling:
- CSV is treated as READ-ONLY seed only.
- App never writes back to CSV.
- You can override dataset path via environment variable INVENTORY_DATASET.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import csv
import os

from django.conf import settings

from .treap_ds_optimized import InventoryTreapOptimized, InventoryItem


# Global in-memory Treap shared across UI + API + CLI.
TREAP = InventoryTreapOptimized(seed=42, search_cache_size=20000)

_LOADED = False


def dataset_path() -> str:
    """Return dataset path, allowing override via env var."""
    override = os.environ.get("INVENTORY_DATASET")
    if override:
        return override
    return str(getattr(settings, "INVENTORY_DATASET_CSV"))


def load_dataset_once() -> None:
    """Load initial inventory dataset into memory (idempotent)."""
    global _LOADED
    if _LOADED:
        return

    path = dataset_path()

    items: List[InventoryItem] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            items.append(InventoryItem(
                sku=row["sku"].strip(),
                name=row["name"].strip(),
                quantity=int(row["quantity"]),
                price=float(row["price"]),
            ))

    # Phase 3 optimization: bulk insert
    TREAP.bulk_insert(items)
    _LOADED = True


# ------------------------- Web/UI helpers -------------------------

def inorder_items() -> List[Dict[str, Any]]:
    return [item_to_dict(it) for it in TREAP.inorder()]


def get_item(sku: str) -> Optional[Dict[str, Any]]:
    it = TREAP.search(sku)
    return item_to_dict(it) if it else None


def add_or_replace_item(sku: str, name: str, quantity: int, price: float) -> Dict[str, Any]:
    it = InventoryItem(sku=sku, name=name, quantity=quantity, price=price)
    TREAP.insert(it)
    return item_to_dict(it)


def delete_item(sku: str) -> bool:
    return TREAP.delete(sku)


def range_items(low: str, high: str) -> List[Dict[str, Any]]:
    return [item_to_dict(it) for it in TREAP.range_query(low, high)]


def change_qty(sku: str, delta: int) -> Dict[str, Any]:
    it = TREAP.update_quantity(sku, delta)
    return item_to_dict(it)


def item_to_dict(it: InventoryItem) -> Dict[str, Any]:
    return {
        "sku": it.sku,
        "name": it.name,
        "quantity": it.quantity,
        "price": round(float(it.price), 2),
    }
