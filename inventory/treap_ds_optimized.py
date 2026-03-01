"""treap_phase3_optimized.py

Phase 3 optimized Treap implementation for dynamic inventory management.

Key optimizations compared to the Phase 2 baseline:
1) Iterative inorder traversal (avoids recursion-depth risk and reduces call overhead).
2) Cached inorder results with a dirty flag (fast repeated listing for UI/CLI).
3) Bounded search cache (SKU -> InventoryItem) for repeated lookups; invalidated on mutations.
4) bulk_insert() to reduce overhead when loading large datasets (single cache invalidation).
5) dataclass(slots=True) to reduce per-item memory overhead.

Treap invariants:
- BST ordering by SKU (string key)
- Heap ordering by random priority (max-heap convention)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List, Dict, Iterable
import random


@dataclass(slots=True)
class InventoryItem:
    """Inventory record stored in the Treap."""
    sku: str
    name: str
    quantity: int
    price: float


class TreapNode:
    """Node in a Treap (BST + Heap)."""
    __slots__ = ("key", "value", "priority", "left", "right")

    def __init__(self, key: str, value: InventoryItem, priority: int) -> None:
        self.key = key
        self.value = value
        self.priority = priority
        self.left: Optional["TreapNode"] = None
        self.right: Optional["TreapNode"] = None


class InventoryTreapOptimized:
    """Optimized Treap wrapper for inventory operations."""

    def __init__(self, seed: Optional[int] = None, search_cache_size: int = 10_000) -> None:
        # Seedable RNG supports reproducible benchmarks.
        self._rng = random.Random(seed)
        self.root: Optional[TreapNode] = None

        # ---- Optimization A: Cached inorder listing ----
        self._dirty: bool = True
        self._inorder_cache: List[InventoryItem] = []

        # ---- Optimization B: Bounded search cache ----
        self._search_cache: Dict[str, InventoryItem] = {}
        self._search_cache_size = max(0, int(search_cache_size))

    # -------------------------- internal cache helpers --------------------------

    def _mark_dirty(self) -> None:
        """Invalidate cached views after any mutation."""
        self._dirty = True
        self._search_cache.clear()

    def _cache_search_put(self, sku: str, item: InventoryItem) -> None:
        """Insert into the bounded search cache with O(1) eviction."""
        if self._search_cache_size <= 0:
            return
        if len(self._search_cache) >= self._search_cache_size:
            # Simple eviction: remove one arbitrary entry (adequate for PoC).
            self._search_cache.pop(next(iter(self._search_cache)))
        self._search_cache[sku] = item

    # ------------------------------- rotations ---------------------------------

    def _rotate_right(self, y: TreapNode) -> TreapNode:
        x = y.left
        assert x is not None
        y.left = x.right
        x.right = y
        return x

    def _rotate_left(self, x: TreapNode) -> TreapNode:
        y = x.right
        assert y is not None
        x.right = y.left
        y.left = x
        return y

    # -------------------------------- core ops --------------------------------

    def insert(self, item: InventoryItem) -> None:
        """Insert or replace (upsert) by SKU."""
        self._mark_dirty()
        priority = self._rng.randint(1, 1_000_000)
        self.root = self._insert(self.root, item.sku, item, priority)

    def bulk_insert(self, items: Iterable[InventoryItem]) -> None:
        """Efficiently insert many items with one cache invalidation."""
        self._mark_dirty()
        for item in items:
            priority = self._rng.randint(1, 1_000_000)
            self.root = self._insert(self.root, item.sku, item, priority)

    def _insert(self, node: Optional[TreapNode], key: str, value: InventoryItem, priority: int) -> TreapNode:
        if node is None:
            return TreapNode(key, value, priority)

        if key < node.key:
            node.left = self._insert(node.left, key, value, priority)
            if node.left and node.left.priority > node.priority:
                node = self._rotate_right(node)
        elif key > node.key:
            node.right = self._insert(node.right, key, value, priority)
            if node.right and node.right.priority > node.priority:
                node = self._rotate_left(node)
        else:
            node.value = value  # upsert
        return node

    def search(self, sku: str) -> Optional[InventoryItem]:
        """Iterative search with bounded cache."""
        if sku in self._search_cache:
            return self._search_cache[sku]

        node = self.root
        while node is not None:
            if sku < node.key:
                node = node.left
            elif sku > node.key:
                node = node.right
            else:
                self._cache_search_put(sku, node.value)
                return node.value
        return None

    def delete(self, sku: str) -> bool:
        """Delete by SKU; returns True if deleted else False."""
        if self.search(sku) is None:
            return False
        self._mark_dirty()
        self.root = self._delete(self.root, sku)
        return True

    def _delete(self, node: Optional[TreapNode], key: str) -> Optional[TreapNode]:
        if node is None:
            return None

        if key < node.key:
            node.left = self._delete(node.left, key)
        elif key > node.key:
            node.right = self._delete(node.right, key)
        else:
            # Node found: rotate it down until it becomes a leaf, then remove.
            if node.left is None and node.right is None:
                return None

            if node.left is None:
                node = self._rotate_left(node)
                node.left = self._delete(node.left, key)
            elif node.right is None:
                node = self._rotate_right(node)
                node.right = self._delete(node.right, key)
            else:
                if node.left.priority > node.right.priority:
                    node = self._rotate_right(node)
                    node.right = self._delete(node.right, key)
                else:
                    node = self._rotate_left(node)
                    node.left = self._delete(node.left, key)

        return node

    # ---------------------------- traversal / query ----------------------------

    def inorder(self) -> List[InventoryItem]:
        """Return items sorted by SKU.

        Optimization: cached inorder list with iterative traversal.
        """
        if not self._dirty:
            return list(self._inorder_cache)

        out: List[InventoryItem] = []
        stack: List[TreapNode] = []
        node = self.root
        while stack or node is not None:
            while node is not None:
                stack.append(node)
                node = node.left
            node = stack.pop()
            out.append(node.value)
            node = node.right

        self._inorder_cache = out
        self._dirty = False
        return list(out)

    def range_query(self, low_sku: str, high_sku: str) -> List[InventoryItem]:
        """Return items with low_sku <= sku <= high_sku."""
        out: List[InventoryItem] = []
        self._range_query(self.root, low_sku, high_sku, out)
        return out

    def _range_query(self, node: Optional[TreapNode], low: str, high: str, out: List[InventoryItem]) -> None:
        if node is None:
            return
        if low < node.key:
            self._range_query(node.left, low, high, out)
        if low <= node.key <= high:
            out.append(node.value)
        if node.key < high:
            self._range_query(node.right, low, high, out)

    # --------------------------- inventory operations --------------------------

    def update_quantity(self, sku: str, delta: int) -> InventoryItem:
        """Adjust quantity by delta; prevents negative stock."""
        item = self.search(sku)
        if item is None:
            raise KeyError(f"SKU not found: {sku}")
        new_qty = item.quantity + delta
        if new_qty < 0:
            raise ValueError("Quantity cannot be negative.")
        item.quantity = new_qty
        self._mark_dirty()
        return item
