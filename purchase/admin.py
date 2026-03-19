from django.contrib import admin
from .models import Vendor, PurchaseOrder, PurchaseOrderLine, PurchaseInvoice, PurchaseReturn


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'gstin', 'is_active', 'company')
    search_fields = ('name', 'gstin')
    list_filter = ('is_active', 'company')


class POLineInline(admin.TabularInline):
    model = PurchaseOrderLine
    extra = 1
    fields = ('line_number', 'product_name', 'quantity', 'received_quantity', 'unit', 'rate', 'gst_rate')


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('po_number', 'vendor_name', 'date', 'total_amount', 'status', 'company')
    list_filter = ('status', 'company')
    search_fields = ('po_number', 'vendor_name')
    inlines = [POLineInline]
    readonly_fields = ('subtotal', 'total_gst', 'total_amount')


@admin.register(PurchaseInvoice)
class PurchaseInvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'vendor_name', 'date', 'total_amount', 'paid_amount', 'status')
    list_filter = ('status', 'company')
    search_fields = ('invoice_number', 'vendor_name')


@admin.register(PurchaseReturn)
class PurchaseReturnAdmin(admin.ModelAdmin):
    list_display = ('return_number', 'vendor_name', 'date', 'total_amount', 'company')
