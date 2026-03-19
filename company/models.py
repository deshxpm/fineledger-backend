"""Company models — multi-company support"""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Company(models.Model):
    """Represents a company/business entity"""
    GST_SCHEME_CHOICES = [('Regular', 'Regular'), ('Composition', 'Composition')]
    CURRENCY_CHOICES = [('INR', 'Indian Rupee'), ('USD', 'US Dollar'), ('EUR', 'Euro')]

    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=50, blank=True)
    gstin = models.CharField(max_length=15, blank=True, verbose_name='GSTIN')
    pan = models.CharField(max_length=10, blank=True, verbose_name='PAN')
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)

    # Financial year
    fy_start = models.DateField(null=True, blank=True)
    fy_end = models.DateField(null=True, blank=True)

    # Settings
    base_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='INR')
    gst_scheme = models.CharField(max_length=20, choices=GST_SCHEME_CHOICES, default='Regular')

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Companies'
        ordering = ['name']

    def __str__(self):
        return self.name


class CompanyUser(models.Model):
    """Links users to companies with role-based access"""
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('accountant', 'Accountant'),
        ('viewer', 'Viewer'),
    ]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='users')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='companies')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer')
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('company', 'user')

    def __str__(self):
        return f'{self.user.username} @ {self.company.name} ({self.role})'
