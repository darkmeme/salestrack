from django.contrib import admin
from .models import Category, Supplier, Product, BranchStock, StockMovement, StockTransfer, StockTransferItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone']
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'category', 'price', 'cost', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'sku']


@admin.register(BranchStock)
class BranchStockAdmin(admin.ModelAdmin):
    list_display = ['product', 'branch', 'quantity']
    list_filter = ['branch']


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['product', 'branch', 'movement_type', 'quantity', 'created_at']
    list_filter = ['movement_type', 'branch']


class StockTransferItemInline(admin.TabularInline):
    model = StockTransferItem
    extra = 0


@admin.register(StockTransfer)
class StockTransferAdmin(admin.ModelAdmin):
    list_display = ['transfer_number', 'origin_branch', 'destination_branch', 'status', 'created_at']
    list_filter = ['status']
    inlines = [StockTransferItemInline]
