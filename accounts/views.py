from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from .models import AccountGroup, Ledger, JournalEntry, JournalLine
from .serializers import (
    AccountGroupSerializer, LedgerSerializer,
    JournalEntrySerializer, JournalEntryCreateSerializer,
    JournalLineSerializer
)


class AccountGroupViewSet(viewsets.ModelViewSet):
    """
    GET    /api/accounts/groups/              — list all groups
    POST   /api/accounts/groups/              — create group
    GET    /api/accounts/groups/{id}/         — retrieve
    PUT    /api/accounts/groups/{id}/         — update
    PATCH  /api/accounts/groups/{id}/         — partial update
    DELETE /api/accounts/groups/{id}/         — delete
    GET    /api/accounts/groups/{id}/ledgers/ — ledgers under this group
    GET    /api/accounts/groups/tree/         — full tree structure
    """
    queryset = AccountGroup.objects.all().select_related('parent')
    serializer_class = AccountGroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['name', 'code']
    filterset_fields = ['nature', 'group_type', 'company']

    def get_queryset(self):
        qs = super().get_queryset()
        company_id = self.request.query_params.get('company')
        if company_id:
            qs = qs.filter(company_id=company_id)
        return qs

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Returns groups structured as a tree (primary → children)"""
        company_id = request.query_params.get('company')
        primary = AccountGroup.objects.filter(group_type='Primary')
        if company_id:
            primary = primary.filter(company_id=company_id)

        result = []
        for group in primary:
            children = AccountGroup.objects.filter(parent=group)
            result.append({
                **AccountGroupSerializer(group).data,
                'children': AccountGroupSerializer(children, many=True).data
            })
        return Response(result)

    @action(detail=True, methods=['get'])
    def ledgers(self, request, pk=None):
        group = self.get_object()
        ledgers = Ledger.objects.filter(group=group)
        return Response(LedgerSerializer(ledgers, many=True).data)


class LedgerViewSet(viewsets.ModelViewSet):
    """
    GET    /api/accounts/ledgers/                 — list ledgers (filterable by nature/group/company)
    POST   /api/accounts/ledgers/                 — create ledger
    GET    /api/accounts/ledgers/{id}/            — retrieve
    PUT    /api/accounts/ledgers/{id}/            — update
    DELETE /api/accounts/ledgers/{id}/            — delete
    GET    /api/accounts/ledgers/{id}/statement/  — account statement (all journal lines)
    """
    queryset = Ledger.objects.all().select_related('group', 'company')
    serializer_class = LedgerSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['name', 'ledger_id']
    filterset_fields = ['company', 'group', 'balance_type', 'is_active']

    def get_queryset(self):
        qs = super().get_queryset()
        company_id = self.request.query_params.get('company')
        nature = self.request.query_params.get('nature')
        if company_id:
            qs = qs.filter(company_id=company_id)
        if nature:
            qs = qs.filter(group__nature=nature)
        return qs

    @action(detail=True, methods=['get'])
    def statement(self, request, pk=None):
        """Return all journal lines for this ledger with running balance"""
        ledger = self.get_object()
        lines = JournalLine.objects.filter(
            ledger=ledger
        ).select_related('entry').order_by('entry__date', 'id')

        running = float(ledger.opening_balance)
        if ledger.opening_balance_type == 'Cr':
            running = -running

        statement = []
        for line in lines:
            amount = float(line.amount)
            if line.entry_type == 'Dr':
                running += amount
            else:
                running -= amount
            statement.append({
                'date': line.entry.date,
                'voucher': line.entry.voucher_number,
                'narration': line.entry.narration or line.narration,
                'debit': amount if line.entry_type == 'Dr' else 0,
                'credit': amount if line.entry_type == 'Cr' else 0,
                'balance': abs(running),
                'balance_type': 'Dr' if running >= 0 else 'Cr',
            })

        return Response({
            'ledger': LedgerSerializer(ledger).data,
            'opening_balance': ledger.opening_balance,
            'opening_balance_type': ledger.opening_balance_type,
            'statement': statement,
            'closing_balance': abs(running),
            'closing_balance_type': 'Dr' if running >= 0 else 'Cr',
        })


class JournalEntryViewSet(viewsets.ModelViewSet):
    """
    GET    /api/accounts/entries/       — list journal entries
    POST   /api/accounts/entries/       — create entry with lines (validates Dr==Cr)
    GET    /api/accounts/entries/{id}/  — retrieve with all lines
    PUT    /api/accounts/entries/{id}/  — update
    DELETE /api/accounts/entries/{id}/  — delete
    POST   /api/accounts/entries/{id}/post/   — mark as posted
    POST   /api/accounts/entries/{id}/unpost/ — revert to draft
    """
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['voucher_number', 'reference', 'narration']
    filterset_fields = ['company', 'voucher_type', 'is_posted']

    def get_queryset(self):
        qs = JournalEntry.objects.all().prefetch_related('lines__ledger').select_related('company')
        company_id = self.request.query_params.get('company')
        if company_id:
            qs = qs.filter(company_id=company_id)
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        return qs.order_by('-date', '-id')

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return JournalEntryCreateSerializer
        return JournalEntrySerializer

    @action(detail=True, methods=['post'])
    def post_entry(self, request, pk=None):
        entry = self.get_object()
        entry.is_posted = True
        entry.save()
        return Response({'status': 'posted', 'id': entry.id})

    @action(detail=True, methods=['post'])
    def unpost(self, request, pk=None):
        entry = self.get_object()
        entry.is_posted = False
        entry.save()
        return Response({'status': 'draft', 'id': entry.id})
