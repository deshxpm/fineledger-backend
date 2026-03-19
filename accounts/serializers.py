from rest_framework import serializers
from .models import AccountGroup, Ledger, JournalEntry, JournalLine


class AccountGroupSerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    level = serializers.IntegerField(read_only=True)

    class Meta:
        model = AccountGroup
        fields = (
            'id', 'company', 'code', 'name', 'group_type', 'nature',
            'parent', 'parent_name', 'description', 'level', 'created_at'
        )
        read_only_fields = ('created_at',)


class LedgerSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source='group.name', read_only=True)
    nature = serializers.CharField(read_only=True)

    class Meta:
        model = Ledger
        fields = (
            'id', 'company', 'ledger_id', 'name', 'group', 'group_name',
            'balance', 'balance_type', 'opening_balance', 'opening_balance_type',
            'nature', 'is_active', 'description', 'created_at'
        )
        read_only_fields = ('created_at',)


class JournalLineSerializer(serializers.ModelSerializer):
    ledger_name = serializers.CharField(source='ledger.name', read_only=True)

    class Meta:
        model = JournalLine
        fields = ('id', 'entry', 'ledger', 'ledger_name', 'entry_type', 'amount', 'narration')


class JournalEntrySerializer(serializers.ModelSerializer):
    lines = JournalLineSerializer(many=True, read_only=True)
    # Convenience flat fields for simple debit/credit (single-line entries)
    debit_ledger_name = serializers.SerializerMethodField()
    credit_ledger_name = serializers.SerializerMethodField()
    entry_amount = serializers.SerializerMethodField()

    class Meta:
        model = JournalEntry
        fields = (
            'id', 'company', 'voucher_number', 'voucher_type', 'date',
            'reference', 'narration', 'is_posted', 'lines',
            'debit_ledger_name', 'credit_ledger_name', 'entry_amount',
            'created_at', 'updated_at'
        )
        read_only_fields = ('created_at', 'updated_at')

    def get_debit_ledger_name(self, obj):
        dr = obj.lines.filter(entry_type='Dr').first()
        return dr.ledger.name if dr else None

    def get_credit_ledger_name(self, obj):
        cr = obj.lines.filter(entry_type='Cr').first()
        return cr.ledger.name if cr else None

    def get_entry_amount(self, obj):
        dr = obj.lines.filter(entry_type='Dr').first()
        return str(dr.amount) if dr else '0.00'


class JournalEntryCreateSerializer(serializers.ModelSerializer):
    """Used for creating entries with inline lines"""
    lines = JournalLineSerializer(many=True)

    class Meta:
        model = JournalEntry
        fields = (
            'company', 'voucher_number', 'voucher_type', 'date',
            'reference', 'narration', 'lines'
        )

    def validate_lines(self, lines):
        total_dr = sum(l['amount'] for l in lines if l['entry_type'] == 'Dr')
        total_cr = sum(l['amount'] for l in lines if l['entry_type'] == 'Cr')
        if total_dr != total_cr:
            raise serializers.ValidationError(
                f'Debit (₹{total_dr}) and Credit (₹{total_cr}) totals must match.'
            )
        return lines

    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        entry = JournalEntry.objects.create(**validated_data)
        for line in lines_data:
            JournalLine.objects.create(entry=entry, **line)
        entry.is_posted = True
        entry.save()
        return entry
