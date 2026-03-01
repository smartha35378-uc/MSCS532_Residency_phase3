import unittest
from inventory.treap_ds import InventoryTreap, InventoryItem


class TestInventoryTreap(unittest.TestCase):
    def setUp(self):
        self.t = InventoryTreap(seed=1)
        self.t.insert(InventoryItem("A2", "Item2", 10, 2.0))
        self.t.insert(InventoryItem("A1", "Item1", 5, 1.0))
        self.t.insert(InventoryItem("A3", "Item3", 7, 3.0))

    def test_inorder_sorted(self):
        skus = [x.sku for x in self.t.inorder()]
        self.assertEqual(skus, ["A1", "A2", "A3"])

    def test_search_found_and_missing(self):
        self.assertIsNotNone(self.t.search("A2"))
        self.assertIsNone(self.t.search("Z9"))

    def test_update_quantity(self):
        self.t.update_quantity("A1", 3)
        self.assertEqual(self.t.search("A1").quantity, 8)
        with self.assertRaises(ValueError):
            self.t.update_quantity("A1", -100)

    def test_delete(self):
        self.assertTrue(self.t.delete("A2"))
        self.assertIsNone(self.t.search("A2"))
        self.assertFalse(self.t.delete("A2"))  # already deleted

    def test_range_query(self):
        items = self.t.range_query("A1", "A2")
        self.assertEqual([x.sku for x in items], ["A1", "A2"])


if __name__ == "__main__":
    unittest.main()
