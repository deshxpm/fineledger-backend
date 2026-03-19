"""Dashboard aggregation URLs and views"""
from django.urls import path
from django.db.models import Sum, Count, Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta


@api_view(['GET'])
def dashboard_overview(request):
    """Aggregate stats for the dashboard overview panel"""
    from accounts.models import Ledger
    from sales.models import SalesDocument
    from purchase.models import PurchaseOrder
    from inventory.models import Product

    # Revenue: sum of all Invoice amounts with Paid status
    revenue = SalesDocument.objects.filter(
        doc_type='Invoice'
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    # Expenses: sum of all paid purchase invoices
    expenses = PurchaseOrder.objects.filter(
        status='Paid'
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    # Receivables: unpaid + overdue invoices
    receivables = SalesDocument.objects.filter(
        doc_type='Invoice',
        status__in=['Pending', 'Overdue']
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    # Net Profit
    net_profit = revenue - expenses

    # Low stock count
    low_stock = Product.objects.filter(
        stock_quantity__lt=models_min_stock()
    ).count()

    # Recent invoices
    recent_invoices = SalesDocument.objects.filter(
        doc_type='Invoice'
    ).order_by('-date')[:5].values(
        'id', 'doc_number', 'customer__name', 'total_amount', 'status', 'date'
    )

    # Sales pipeline counts
    pipeline = {}
    for doc_type in ['Quotation', 'Proforma', 'Order', 'Challan', 'Invoice']:
        pipeline[doc_type] = SalesDocument.objects.filter(doc_type=doc_type).count()

    # Account balances
    top_ledgers = Ledger.objects.select_related('group').order_by('name')[:5].values(
        'id', 'ledger_id', 'name', 'group__name', 'balance', 'balance_type'
    )

    return Response({
        'stats': {
            'total_revenue': revenue,
            'total_expenses': expenses,
            'receivables': receivables,
            'net_profit': net_profit,
        },
        'recent_invoices': list(recent_invoices),
        'sales_pipeline': pipeline,
        'top_ledgers': list(top_ledgers),
    })


def models_min_stock():
    """Helper to avoid circular import issues"""
    from inventory.models import Product
    from django.db.models import F
    return F('min_stock_level')


@api_view(['GET'])
def low_stock_alert(request):
    """Products below minimum stock level"""
    from inventory.models import Product
    from django.db.models import F
    low = Product.objects.filter(
        stock_quantity__lt=F('min_stock_level')
    ).values('id', 'sku', 'name', 'stock_quantity', 'min_stock_level', 'category__name')
    return Response(list(low))


urlpatterns = [
    path('overview/', dashboard_overview, name='dashboard-overview'),
    path('low-stock/', low_stock_alert, name='dashboard-low-stock'),
]
