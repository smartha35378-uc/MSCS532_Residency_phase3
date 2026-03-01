"""inventory.treap_ds

A Treap (Tree + Heap) implementation tailored for dynamic inventory management.
- BST property by SKU (string key)
- Heap property by randomly assigned priority (max-heap convention here)

This module is independent of Django and can be unit-tested in isolation.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Tuple, Iterable
import random


@dataclass
class InventoryItem:
    """Represents one inventory record stored in the Treap."""
    sku: str
    name: str
    quantity: int
    price: float


class TreapNode:
    """A single node in the Treap."""

    __slots__ = ("key", "value", "priority", "left", "right")

    def __init__(self, key: str, value: InventoryItem, priority: int) -> None:
        self.key: str = key
        self.value: InventoryItem = value

        # Priority enforces balancing. We use a max-heap: parent.priority >= children.priority.
        self.priority: int = priority

        # Left/right children for the BST structure.
        self.left: Optional["TreapNode"] = None
        self.right: Optional["TreapNode"] = None


class InventoryTreap:
    """Treap wrapper providing inventory-centric operations.

    Notes on complexity (expected):
    - insert/search/delete: O(log n) average, O(n) worst-case (rare with good randomness)
    - inorder traversal: O(n)
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        # Allow deterministic priorities for reproducible demos/tests.
        self._rng = random.Random(seed)
        self.root: Optional[TreapNode] = None

    # ----------------------------- Rotations -----------------------------
    # Rotations preserve BST ordering but repair heap property violations.

    def _rotate_right(self, y: TreapNode) -> TreapNode:
        """Right rotation around node y."""
        x = y.left
        assert x is not None  # for type-checkers; rotation requires left child

        # Perform rotation
        y.left = x.right
        x.right = y
        return x

    def _rotate_left(self, x: TreapNode) -> TreapNode:
        """Left rotation around node x."""
        y = x.right
        assert y is not None  # rotation requires right child

        # Perform rotation
        x.right = y.left
        y.left = x
        return y

    # ----------------------------- Core Ops -----------------------------

    def insert(self, item: InventoryItem) -> None:
        """Insert or replace an item by SKU.

        If the SKU already exists, we replace the stored InventoryItem
        (common 'upsert' pattern for inventory systems).
        """
        priority = self._rng.randint(1, 1_000_000)
        self.root = self._insert(self.root, item.sku, item, priority)

    def _insert(self, node: Optional[TreapNode], key: str, value: InventoryItem, priority: int) -> TreapNode:
        # Standard BST insert first.
        if node is None:
            return TreapNode(key, value, priority)

        if key < node.key:
            node.left = self._insert(node.left, key, value, priority)

            # Heap repair: if child priority is greater, rotate right.
            if node.left and node.left.priority > node.priority:
                node = self._rotate_right(node)

        elif key > node.key:
            node.right = self._insert(node.right, key, value, priority)

            # Heap repair: if child priority is greater, rotate left.
            if node.right and node.right.priority > node.priority:
                node = self._rotate_left(node)

        else:
            # Same key => replace value, keep node priority (stability).
            node.value = value

        return node

    def search(self, sku: str) -> Optional[InventoryItem]:
        """Return the InventoryItem for sku, or None if not found."""
        node = self.root
        while node is not None:
            if sku < node.key:
                node = node.left
            elif sku > node.key:
                node = node.right
            else:
                return node.value
        return None

    def delete(self, sku: str) -> bool:
        """Delete item by SKU. Returns True if deleted, False if missing."""
        before = self.search(sku) is not None
        if not before:
            return False
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
            # Node found. If it's a leaf, remove it directly.
            if node.left is None and node.right is None:
                return None

            # If one child is missing, rotate toward the existing child to move the target down.
            if node.left is None:
                node = self._rotate_left(node)
                node.left = self._delete(node.left, key)
            elif node.right is None:
                node = self._rotate_right(node)
                node.right = self._delete(node.right, key)
            else:
                # Both children exist: rotate the higher-priority child up,
                # pushing the node down until it becomes a leaf.
                if node.left.priority > node.right.priority:
                    node = self._rotate_right(node)
                    node.right = self._delete(node.right, key)
                else:
                    node = self._rotate_left(node)
                    node.left = self._delete(node.left, key)

        return node

    def inorder(self) -> List[InventoryItem]:
        """Return items sorted by SKU."""
        out: List[InventoryItem] = []
        self._inorder(self.root, out)
        return out

    def _inorder(self, node: Optional[TreapNode], out: List[InventoryItem]) -> None:
        if node is None:
            return
        self._inorder(node.left, out)
        out.append(node.value)
        self._inorder(node.right, out)

    # ----------------------------- Inventory Ops -----------------------------

    def update_quantity(self, sku: str, delta: int) -> InventoryItem:
        """Add/subtract quantity for an existing SKU.

        Raises:
            KeyError: if the SKU doesn't exist.
            ValueError: if the resulting quantity would be negative.
        """
        item = self.search(sku)
        if item is None:
            raise KeyError(f"SKU not found: {sku}")
        new_qty = item.quantity + delta
        if new_qty < 0:
            raise ValueError("Quantity cannot be negative.")
        item.quantity = new_qty
        return item

    def set_quantity(self, sku: str, qty: int) -> InventoryItem:
        """Set quantity for an existing SKU."""
        if qty < 0:
            raise ValueError("Quantity cannot be negative.")
        item = self.search(sku)
        if item is None:
            raise KeyError(f"SKU not found: {sku}")
        item.quantity = qty
        return item

    def range_query(self, low_sku: str, high_sku: str) -> List[InventoryItem]:
        """Return all items with low_sku <= sku <= high_sku (sorted by SKU)."""
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
