"""
Sales models — full sales pipeline:
  Quotation → Proforma Invoice → Sales Order → Delivery Challan → Invoice
"""
from django.db import models
from company.models import Company
from django.core.validators import MinValueValidator
from decimal import Decimal


class Customer(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='customers')
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    gstin = models.CharField(max_length=15, blank=True)
    pan = models.CharField(max_length=10, blank=True)
    billing_address = models.TextField(blank=True)
    shipping_address = models.TextField(blank=True)
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class SalesDocument(models.Model):
    """Single model handles all 5 sales document types"""
    DOC_TYPE_CHOICES = [
        ('Quotation', 'Quotation'),
        ('Proforma', 'Proforma Invoice'),
        ('Order', 'Sales Order'),
        ('Challan', 'Delivery Challan'),
        ('Invoice', 'Invoice'),
    ]
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Confirmed', 'Confirmed'),
        ('Dispatched', 'Dispatched'),
        ('Paid', 'Paid'),
        ('Overdue', 'Overdue'),
        ('Converted', 'Converted'),
        ('Cancelled', 'Cancelled'),
    ]
    GST_TYPE_CHOICES = [('IGST', 'IGST'), ('CGST+SGST', 'CGST + SGST')]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='sales_documents')
    doc_type = models.CharField(max_length=20, choices=DOC_TYPE_CHOICES)
    doc_number = models.CharField(max_length=30)
    date = models.DateField()
    due_date = models.DateField(null=True, blank=True)

    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT,
        related_name='sales_documents', null=True, blank=True
    )
    customer_name = models.CharField(max_length=200, blank=True)  # fallback if no FK
    billing_address = models.TextField(blank=True)
    shipping_address = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    gst_type = models.CharField(max_length=20, choices=GST_TYPE_CHOICES, default='CGST+SGST')

    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_gst = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    notes = models.TextField(blank=True)
    terms = models.TextField(blank=True)

    # Track document lineage (e.g. Invoice converted from Challan)
    parent_document = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='child_documents'
    )

    created_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('company', 'doc_number')
        ordering = ['-date', '-id']

    def __str__(self):
        return f'{self.doc_number} — {self.customer_name or (self.customer.name if self.customer else "")}'

    def recalculate_totals(self):
        """Recompute subtotal, GST and total from lines"""
        lines = self.lines.all()
        self.subtotal = sum(l.line_total for l in lines)
        self.total_gst = sum(l.gst_amount for l in lines)
        self.total_amount = self.subtotal + self.total_gst - self.discount
        self.save(update_fields=['subtotal', 'total_gst', 'total_amount'])


class SalesDocumentLine(models.Model):
    """Line items on any sales document"""
    GST_RATE_CHOICES = [
        (Decimal('0'), '0%'),
        (Decimal('5'), '5%'),
        (Decimal('12'), '12%'),
        (Decimal('18'), '18%'),
        (Decimal('28'), '28%'),
    ]

    document = models.ForeignKey(
        SalesDocument, on_delete=models.CASCADE, related_name='lines'
    )
    line_number = models.PositiveIntegerField(default=1)
    product_name = models.CharField(max_length=200)
    product_sku = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    quantity = models.DecimalField(
        max_digits=10, decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))]
    )
    unit = models.CharField(max_length=20, default='pcs')
    rate = models.DecimalField(max_digits=15, decimal_places=2)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=18)
    discount_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    @property
    def line_total_before_discount(self):
        return self.quantity * self.rate

    @property
    def discount_amount(self):
        return self.line_total_before_discount * self.discount_pct / 100

    @property
    def taxable_amount(self):
        return self.line_total_before_discount - self.discount_amount

    @property
    def gst_amount(self):
        return self.taxable_amount * self.gst_rate / 100

    @property
    def line_total(self):
        return self.taxable_amount

    @property
    def line_total_with_gst(self):
        return self.taxable_amount + self.gst_amount

    class Meta:
        ordering = ['line_number']

    def __str__(self):
        return f'{self.document.doc_number} — line {self.line_number}: {self.product_name}'
