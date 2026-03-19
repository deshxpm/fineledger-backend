"""
Accounts models:
  - AccountGroup   (Chart of Accounts groups & subgroups)
  - Ledger         (Individual account ledgers)
  - JournalEntry   (Voucher header)
  - JournalLine    (Double-entry lines)
"""
from django.db import models
from company.models import Company
from django.core.exceptions import ValidationError


class AccountGroup(models.Model):
    """Account groups / Chart of Accounts structure"""
    TYPE_CHOICES = [('Primary', 'Primary'), ('Sub-Group', 'Sub-Group')]
    NATURE_CHOICES = [
        ('Asset', 'Asset'),
        ('Liability', 'Liability'),
        ('Income', 'Income'),
        ('Expense', 'Expense'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='account_groups')
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    group_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='Primary')
    nature = models.CharField(max_length=20, choices=NATURE_CHOICES)
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='children'
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('company', 'code')
        ordering = ['code']

    def __str__(self):
        return f'{self.code} — {self.name}'

    @property
    def level(self):
        return 0 if self.group_type == 'Primary' else 1


class Ledger(models.Model):
    """Individual account ledger"""
    BALANCE_TYPE_CHOICES = [('Dr', 'Debit'), ('Cr', 'Credit')]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='ledgers')
    ledger_id = models.CharField(max_length=20)  # e.g. L001
    name = models.CharField(max_length=200)
    group = models.ForeignKey(AccountGroup, on_delete=models.PROTECT, related_name='ledgers')
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_type = models.CharField(max_length=2, choices=BALANCE_TYPE_CHOICES, default='Dr')
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    opening_balance_type = models.CharField(max_length=2, choices=BALANCE_TYPE_CHOICES, default='Dr')
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('company', 'ledger_id')
        ordering = ['name']

    def __str__(self):
        return f'{self.ledger_id} — {self.name}'

    @property
    def nature(self):
        return self.group.nature


class JournalEntry(models.Model):
    """Journal voucher header"""
    VOUCHER_TYPES = [
        ('Journal', 'Journal'),
        ('Payment', 'Payment'),
        ('Receipt', 'Receipt'),
        ('Contra', 'Contra'),
        ('Sales', 'Sales'),
        ('Purchase', 'Purchase'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='journal_entries')
    voucher_number = models.CharField(max_length=30)  # e.g. JV-001
    voucher_type = models.CharField(max_length=20, choices=VOUCHER_TYPES, default='Journal')
    date = models.DateField()
    reference = models.CharField(max_length=50, blank=True)
    narration = models.TextField(blank=True)
    is_posted = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='journal_entries'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('company', 'voucher_number')
        ordering = ['-date', '-id']

    def __str__(self):
        return f'{self.voucher_number} ({self.date})'

    def clean(self):
        """Validate that debits == credits"""
        if self.pk:
            total_dr = sum(l.amount for l in self.lines.filter(entry_type='Dr'))
            total_cr = sum(l.amount for l in self.lines.filter(entry_type='Cr'))
            if total_dr != total_cr:
                raise ValidationError('Debit and Credit totals must match.')


class JournalLine(models.Model):
    """Individual debit/credit line in a journal entry"""
    ENTRY_TYPE_CHOICES = [('Dr', 'Debit'), ('Cr', 'Credit')]

    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    ledger = models.ForeignKey(Ledger, on_delete=models.PROTECT, related_name='journal_lines')
    entry_type = models.CharField(max_length=2, choices=ENTRY_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    narration = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.entry_type} ₹{self.amount} — {self.ledger.name}'
