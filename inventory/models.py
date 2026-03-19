"""
Inventory models:
  - Category
  - Product
  - StockMovement  (audit trail for every stock change)
"""
from django.db import models
from company.models import Company
from django.core.validators import MinValueValidator
from decimal import Decimal


class Category(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='subcategories'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']
        unique_together = ('company', 'name')

    def __str__(self):
        return self.name


class Product(models.Model):
    UNIT_CHOICES = [
        ('pcs', 'Pieces'),
        ('kgs', 'Kilograms'),
        ('mtrs', 'Metres'),
        ('ltrs', 'Litres'),
        ('sets', 'Sets'),
        ('box', 'Box'),
        ('nos', 'Numbers'),
    ]
    GST_RATE_CHOICES = [
        (Decimal('0'), '0%'),
        (Decimal('5'), '5%'),
        (Decimal('12'), '12%'),
        (Decimal('18'), '18%'),
        (Decimal('28'), '28%'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='products')
    sku = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='products'
    )
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='pcs')

    # Pricing
    cost_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    mrp = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=18)
    hsn_code = models.CharField(max_length=20, blank=True)

    # Stock
    stock_quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    min_stock_level = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    max_stock_level = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    reorder_quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0)

    is_active = models.BooleanField(default=True)
    is_taxable = models.BooleanField(default=True)
    track_inventory = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('company', 'sku')
        ordering = ['name']

    def __str__(self):
        return f'{self.sku} — {self.name}'

    @property
    def is_low_stock(self):
        return self.stock_quantity < self.min_stock_level

    @property
    def stock_value(self):
        return self.stock_quantity * self.cost_price


class StockMovement(models.Model):
    """Audit log for all stock in/out movements"""
    MOVEMENT_TYPE_CHOICES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('ADJUST', 'Adjustment'),
        ('OPENING', 'Opening Stock'),
        ('RETURN_IN', 'Return In'),
        ('RETURN_OUT', 'Return Out'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='stock_movements')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES)
    quantity = models.DecimalField(
        max_digits=12, decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))]
    )
    balance_after = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    unit_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    reference = models.CharField(max_length=50, blank=True)  # e.g. PO-001 or INV-004
    notes = models.TextField(blank=True)
    date = models.DateField()
    created_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f'{self.movement_type} {self.quantity} {self.product.name}'
