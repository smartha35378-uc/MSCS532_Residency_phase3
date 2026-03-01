from django.urls import path
from . import views

urlpatterns = [
    # ---------------- UI routes (HTML) ----------------
    path("", views.ui_home, name="ui_home"),
    path("ui/items/", views.ui_items, name="ui_items"),
    path("ui/items/add/", views.ui_add, name="ui_add"),
    path("ui/items/range/", views.ui_range, name="ui_range"),
    path("ui/items/<str:sku>/", views.ui_detail, name="ui_detail"),
    path("ui/items/<str:sku>/qty/", views.ui_update_qty, name="ui_update_qty"),
    path("ui/items/<str:sku>/delete/", views.ui_delete, name="ui_delete"),

    # ---------------- API routes (JSON) ----------------
    path("api/", views.index, name="index"),
    path("api/items/", views.items_inorder, name="items_inorder"),
    path("api/items/<str:sku>/", views.item_detail, name="item_detail"),
    path("api/items/range/", views.items_range, name="items_range"),
    path("api/items/add/", views.item_add, name="item_add"),
    path("api/items/<str:sku>/qty/", views.item_update_qty, name="item_update_qty"),
    path("api/items/<str:sku>/delete/", views.item_delete, name="item_delete"),
]
