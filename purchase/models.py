"""
Purchase models:
  - Vendor
  - PurchaseOrder
  - PurchaseOrderLine
  - PurchaseInvoice  (linked to PO)
  - PurchaseReturn
"""
from django.db import models
from company.models import Company
from django.core.validators import MinValueValidator
from decimal import Decimal


class Vendor(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='vendors')
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    gstin = models.CharField(max_length=15, blank=True)
    pan = models.CharField(max_length=10, blank=True)
    address = models.TextField(blank=True)
    payment_terms = models.CharField(max_length=100, blank=True)  # e.g. "Net 30"
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Sent', 'Sent'),
        ('Pending', 'Pending'),
        ('Partial', 'Partially Received'),
        ('Received', 'Fully Received'),
        ('Paid', 'Paid'),
        ('Cancelled', 'Cancelled'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='purchase_orders')
    po_number = models.CharField(max_length=30)
    date = models.DateField()
    expected_delivery = models.DateField(null=True, blank=True)

    vendor = models.ForeignKey(
        Vendor, on_delete=models.PROTECT,
        related_name='purchase_orders', null=True, blank=True
    )
    vendor_name = models.CharField(max_length=200, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')

    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_gst = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('company', 'po_number')
        ordering = ['-date', '-id']

    def __str__(self):
        return self.po_number

    def recalculate_totals(self):
        lines = self.lines.all()
        self.subtotal = sum(l.taxable_amount for l in lines)
        self.total_gst = sum(l.gst_amount for l in lines)
        self.total_amount = self.subtotal + self.total_gst
        self.save(update_fields=['subtotal', 'total_gst', 'total_amount'])


class PurchaseOrderLine(models.Model):
    purchase_order = models.ForeignKey(
        PurchaseOrder, on_delete=models.CASCADE, related_name='lines'
    )
    line_number = models.PositiveIntegerField(default=1)
    product_name = models.CharField(max_length=200)
    product_sku = models.CharField(max_length=50, blank=True)
    quantity = models.DecimalField(
        max_digits=10, decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))]
    )
    received_quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    unit = models.CharField(max_length=20, default='pcs')
    rate = models.DecimalField(max_digits=15, decimal_places=2)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=18)

    @property
    def taxable_amount(self):
        return self.quantity * self.rate

    @property
    def gst_amount(self):
        return self.taxable_amount * self.gst_rate / 100

    @property
    def line_total(self):
        return self.taxable_amount + self.gst_amount

    @property
    def pending_quantity(self):
        return self.quantity - self.received_quantity

    class Meta:
        ordering = ['line_number']

    def __str__(self):
        return f'{self.purchase_order.po_number} — {self.product_name}'


class PurchaseInvoice(models.Model):
    """Vendor invoice linked to a PO"""
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Partial', 'Partial'),
        ('Overdue', 'Overdue'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='purchase_invoices')
    invoice_number = models.CharField(max_length=30)
    vendor_invoice_number = models.CharField(max_length=50, blank=True)
    date = models.DateField()
    due_date = models.DateField(null=True, blank=True)

    purchase_order = models.ForeignKey(
        PurchaseOrder, on_delete=models.PROTECT,
        related_name='invoices', null=True, blank=True
    )
    vendor = models.ForeignKey(
        Vendor, on_delete=models.PROTECT, related_name='invoices', null=True, blank=True
    )
    vendor_name = models.CharField(max_length=200, blank=True)

    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_gst = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('company', 'invoice_number')
        ordering = ['-date', '-id']

    def __str__(self):
        return self.invoice_number

    @property
    def balance_due(self):
        return self.total_amount - self.paid_amount


class PurchaseReturn(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='purchase_returns')
    return_number = models.CharField(max_length=30)
    date = models.DateField()
    purchase_invoice = models.ForeignKey(
        PurchaseInvoice, on_delete=models.PROTECT,
        related_name='returns', null=True, blank=True
    )
    vendor = models.ForeignKey(
        Vendor, on_delete=models.PROTECT, related_name='returns', null=True, blank=True
    )
    vendor_name = models.CharField(max_length=200, blank=True)
    reason = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return self.return_number
