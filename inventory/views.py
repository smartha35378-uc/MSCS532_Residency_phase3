"""inventory.views

This PoC provides TWO interfaces:
1) Web UI (HTML templates) under /ui/...
2) JSON API under /api/...
"""

from __future__ import annotations
from typing import Any, Dict, Optional

from django.http import JsonResponse, HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt

from . import services


# Load initial dataset on first import of views.
# NOTE: In production you'd use AppConfig.ready() or a startup hook.
services.load_dataset_once()


# ---------------------------------------------------------------------
# UI (HTML) views
# ---------------------------------------------------------------------

@require_GET
def ui_home(request: HttpRequest) -> HttpResponse:
    return render(request, "inventory/home.html")


@require_GET
def ui_items(request: HttpRequest) -> HttpResponse:
    """Show all items sorted by SKU, with optional SKU search."""
    sku = (request.GET.get("sku") or "").strip()
    searched = False
    item: Optional[Dict[str, Any]] = None

    if sku:
        searched = True
        item = services.get_item(sku)

    context = {
        "items": services.inorder_items(),
        "sku": sku,
        "searched": searched,
        "item": item,
    }
    return render(request, "inventory/items.html", context)


@require_GET
def ui_detail(request: HttpRequest, sku: str) -> HttpResponse:
    item = services.get_item(sku)
    if item is None:
        return render(request, "inventory/base.html", {
            "message": f"SKU not found: {sku}",
            "message_type": "err",
        }, status=404)
    return render(request, "inventory/detail.html", {"item": item})


def ui_add(request: HttpRequest) -> HttpResponse:
    """Add or replace an item (upsert)."""
    if request.method == "GET":
        return render(request, "inventory/add.html", {"form": {}})

    # POST
    sku = (request.POST.get("sku") or "").strip()
    name = (request.POST.get("name") or "").strip()
    quantity_raw = request.POST.get("quantity") or ""
    price_raw = request.POST.get("price") or ""

    form = {"sku": sku, "name": name, "quantity": quantity_raw, "price": price_raw}

    # Basic validation with friendly error messages for the UI.
    if not sku or not name:
        return render(request, "inventory/add.html", {
            "form": form,
            "message": "SKU and Name are required.",
            "message_type": "err",
        }, status=400)

    try:
        quantity = int(quantity_raw)
        price = float(price_raw)
        if quantity < 0 or price < 0:
            raise ValueError
    except ValueError:
        return render(request, "inventory/add.html", {
            "form": form,
            "message": "Quantity must be an integer >= 0; Price must be a number >= 0.",
            "message_type": "err",
        }, status=400)

    item = services.add_or_replace_item(sku, name, quantity, price)
    return render(request, "inventory/add.html", {
        "form": {},
        "message": f"Saved item {sku}.",
        "message_type": "ok",
    })


def ui_update_qty(request: HttpRequest, sku: str) -> HttpResponse:
    """Apply a delta to an item's quantity."""
    if request.method != "POST":
        return redirect("ui_detail", sku=sku)

    try:
        delta = int(request.POST.get("delta") or "0")
    except ValueError:
        return render(request, "inventory/base.html", {
            "message": "Delta must be an integer.",
            "message_type": "err",
        }, status=400)

    try:
        services.change_qty(sku, delta)
    except KeyError:
        return render(request, "inventory/base.html", {
            "message": f"SKU not found: {sku}",
            "message_type": "err",
        }, status=404)
    except ValueError as e:
        return render(request, "inventory/base.html", {
            "message": str(e),
            "message_type": "err",
        }, status=400)

    return redirect("ui_detail", sku=sku)


def ui_delete(request: HttpRequest, sku: str) -> HttpResponse:
    """Delete an item by SKU."""
    if request.method != "POST":
        return redirect("ui_detail", sku=sku)

    deleted = services.delete_item(sku)
    if not deleted:
        return render(request, "inventory/base.html", {
            "message": f"SKU not found: {sku}",
            "message_type": "err",
        }, status=404)

    return redirect("ui_items")


@require_GET
def ui_range(request: HttpRequest) -> HttpResponse:
    low = (request.GET.get("low") or "").strip()
    high = (request.GET.get("high") or "").strip()

    ran = bool(low and high)
    items = services.range_items(low, high) if ran else []

    return render(request, "inventory/range.html", {
        "low": low,
        "high": high,
        "ran": ran,
        "items": items,
    })


# ---------------------------------------------------------------------
# API (JSON) endpoints — kept for testing/automation
# ---------------------------------------------------------------------

@require_GET
def index(request: HttpRequest) -> JsonResponse:
    return JsonResponse({
        "message": "Inventory Treap PoC API",
        "ui": {
            "home": "/",
            "items": "/ui/items/",
            "add": "/ui/items/add/",
            "range": "/ui/items/range/",
        },
        "endpoints": {
            "GET /api/items/": "List all items (inorder by SKU)",
            "GET /api/items/<sku>/": "Get one item by SKU",
            "GET /api/items/range/?low=A1000&high=C3999": "Range query by SKU",
            "POST /api/items/add/": "Add or replace item (sku,name,quantity,price)",
            "POST /api/items/<sku>/qty/": "Update quantity by delta (delta=int)",
            "POST /api/items/<sku>/delete/": "Delete item by SKU",
        }
    })


@require_GET
def items_inorder(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"items": services.inorder_items()})


@require_GET
def item_detail(request: HttpRequest, sku: str) -> JsonResponse:
    item = services.get_item(sku)
    if item is None:
        return JsonResponse({"error": f"SKU not found: {sku}"}, status=404)
    return JsonResponse(item)


@require_GET
def items_range(request: HttpRequest) -> JsonResponse:
    low = request.GET.get("low", "")
    high = request.GET.get("high", "")
    if not low or not high:
        return JsonResponse({"error": "Provide query params: low and high"}, status=400)
    return JsonResponse({"items": services.range_items(low, high)})


# For PoC simplicity we exempt CSRF on API routes; UI routes keep CSRF.
@csrf_exempt
@require_POST
def item_add(request: HttpRequest) -> JsonResponse:
    data = request.POST
    try:
        sku = data["sku"].strip()
        name = data["name"].strip()
        quantity = int(data["quantity"])
        price = float(data["price"])
        if quantity < 0 or price < 0:
            return JsonResponse({"error": "quantity and price must be non-negative"}, status=400)
    except KeyError as e:
        return JsonResponse({"error": f"Missing field: {e.args[0]} (required: sku,name,quantity,price)"}, status=400)
    except ValueError:
        return JsonResponse({"error": "quantity must be int; price must be float"}, status=400)

    item = services.add_or_replace_item(sku, name, quantity, price)
    return JsonResponse({"upserted": item}, status=201)


@csrf_exempt
@require_POST
def item_update_qty(request: HttpRequest, sku: str) -> JsonResponse:
    try:
        delta = int(request.POST.get("delta", "0"))
    except ValueError:
        return JsonResponse({"error": "delta must be int"}, status=400)

    try:
        item = services.change_qty(sku, delta)
    except KeyError:
        return JsonResponse({"error": f"SKU not found: {sku}"}, status=404)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"updated": item})


@csrf_exempt
@require_POST
def item_delete(request: HttpRequest, sku: str) -> JsonResponse:
    deleted = services.delete_item(sku)
    if not deleted:
        return JsonResponse({"error": f"SKU not found: {sku}"}, status=404)
    return JsonResponse({"deleted": sku})
