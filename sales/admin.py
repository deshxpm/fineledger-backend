from django.contrib import admin
from .models import Customer, SalesDocument, SalesDocumentLine


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'gstin', 'is_active', 'company')
    search_fields = ('name', 'email', 'gstin')
    list_filter = ('is_active', 'company')


class SalesDocumentLineInline(admin.TabularInline):
    model = SalesDocumentLine
    extra = 1
    fields = ('line_number', 'product_name', 'quantity', 'unit', 'rate', 'gst_rate', 'discount_pct')
    readonly_fields = ()


@admin.register(SalesDocument)
class SalesDocumentAdmin(admin.ModelAdmin):
    list_display = ('doc_number', 'doc_type', 'customer_name', 'date', 'total_amount', 'status', 'company')
    list_filter = ('doc_type', 'status', 'company')
    search_fields = ('doc_number', 'customer_name')
    inlines = [SalesDocumentLineInline]
    readonly_fields = ('subtotal', 'total_gst', 'total_amount', 'created_at', 'updated_at')
