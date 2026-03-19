from django.contrib import admin
from .models import AccountGroup, Ledger, JournalEntry, JournalLine


@admin.register(AccountGroup)
class AccountGroupAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'group_type', 'nature', 'parent', 'company')
    list_filter = ('group_type', 'nature', 'company')
    search_fields = ('code', 'name')


@admin.register(Ledger)
class LedgerAdmin(admin.ModelAdmin):
    list_display = ('ledger_id', 'name', 'group', 'balance', 'balance_type', 'company', 'is_active')
    list_filter = ('balance_type', 'is_active', 'company')
    search_fields = ('ledger_id', 'name')


class JournalLineInline(admin.TabularInline):
    model = JournalLine
    extra = 2
    fields = ('ledger', 'entry_type', 'amount', 'narration')


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ('voucher_number', 'voucher_type', 'date', 'reference', 'narration', 'is_posted')
    list_filter = ('voucher_type', 'is_posted', 'company')
    search_fields = ('voucher_number', 'reference', 'narration')
    inlines = [JournalLineInline]
