from django.contrib import admin
from .models import Customer, Sale, SaleItem, Payment


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'created_at']
    search_fields = ['name', 'email']


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ['subtotal']


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'branch', 'customer', 'seller', 'total', 'status', 'created_at']
    list_filter = ['status', 'branch']
    search_fields = ['invoice_number']
    inlines = [SaleItemInline, PaymentInline]
    readonly_fields = ['invoice_number', 'subtotal', 'tax', 'total']
