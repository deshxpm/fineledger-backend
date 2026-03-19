from django.contrib import admin
from .models import Category, Product, StockMovement


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'company')
    search_fields = ('name',)
    list_filter = ('company',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'sku', 'name', 'category', 'unit',
        'stock_quantity', 'min_stock_level',
        'cost_price', 'selling_price', 'is_active', 'company'
    )
    list_filter = ('is_active', 'category', 'company')
    search_fields = ('sku', 'name', 'hsn_code')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('product', 'movement_type', 'quantity', 'balance_after', 'reference', 'date', 'company')
    list_filter = ('movement_type', 'company')
    search_fields = ('product__name', 'product__sku', 'reference')
    readonly_fields = ('created_at',)
