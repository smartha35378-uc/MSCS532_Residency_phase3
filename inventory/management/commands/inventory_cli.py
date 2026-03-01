"""Django management command: inventory_cli

This provides a simple **CLI interface** to the in-memory Treap.

Run:
    python manage.py inventory_cli

Why a management command?
- It uses Django settings (so it knows where the read-only CSV is)
- It can share the same service layer as the web UI and API
"""

from __future__ import annotations
from django.core.management.base import BaseCommand
from inventory import services


HELP_TEXT = """\
Commands:
  help
  list
  search <SKU>
  add <SKU> <NAME> <QTY> <PRICE>
  qty <SKU> <DELTA>
  delete <SKU>
  range <LOW_SKU> <HIGH_SKU>
  exit

Notes:
  - The dataset CSV is READ-ONLY and is only used for initial seeding.
  - 'add' is an UPSERT (replaces existing SKU if it already exists).
"""


class Command(BaseCommand):
    help = "Interactive CLI for the Inventory Treap PoC"

    def handle(self, *args, **options):
        # Ensure dataset is loaded (idempotent).
        services.load_dataset_once()

        self.stdout.write(self.style.SUCCESS("Inventory Treap CLI (type 'help' for commands)"))
        while True:
            try:
                raw = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                self.stdout.write("\nExiting.")
                return

            if not raw:
                continue

            parts = raw.split()
            cmd = parts[0].lower()

            try:
                if cmd in ("exit", "quit"):
                    self.stdout.write("Exiting.")
                    return

                if cmd == "help":
                    self.stdout.write(HELP_TEXT)
                    continue

                if cmd == "list":
                    items = services.inorder_items()
                    for it in items:
                        self.stdout.write(f"{it['sku']}: {it['name']} | qty={it['quantity']} | price=${it['price']}")
                    continue

                if cmd == "search" and len(parts) == 2:
                    sku = parts[1]
                    it = services.get_item(sku)
                    if not it:
                        self.stdout.write(self.style.WARNING(f"Not found: {sku}"))
                    else:
                        self.stdout.write(f"{it['sku']}: {it['name']} | qty={it['quantity']} | price=${it['price']}")
                    continue

                if cmd == "add" and len(parts) >= 5:
                    sku = parts[1]
                    # NAME may contain spaces, so we parse from the end:
                    qty = int(parts[-2])
                    price = float(parts[-1])
                    name = " ".join(parts[2:-2])
                    if qty < 0 or price < 0:
                        raise ValueError("qty and price must be non-negative")
                    it = services.add_or_replace_item(sku, name, qty, price)
                    self.stdout.write(self.style.SUCCESS(f"Saved: {it['sku']}"))
                    continue

                if cmd == "qty" and len(parts) == 3:
                    sku = parts[1]
                    delta = int(parts[2])
                    it = services.change_qty(sku, delta)
                    self.stdout.write(self.style.SUCCESS(f"Updated qty: {it['sku']} -> {it['quantity']}"))
                    continue

                if cmd == "delete" and len(parts) == 2:
                    sku = parts[1]
                    ok = services.delete_item(sku)
                    if not ok:
                        self.stdout.write(self.style.WARNING(f"Not found: {sku}"))
                    else:
                        self.stdout.write(self.style.SUCCESS(f"Deleted: {sku}"))
                    continue

                if cmd == "range" and len(parts) == 3:
                    low, high = parts[1], parts[2]
                    items = services.range_items(low, high)
                    for it in items:
                        self.stdout.write(f"{it['sku']}: {it['name']} | qty={it['quantity']} | price=${it['price']}")
                    continue

                self.stdout.write(self.style.WARNING("Unrecognized command or wrong arguments. Type 'help'."))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error: {e}"))
