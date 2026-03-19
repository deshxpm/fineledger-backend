from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Vendor, PurchaseOrder, PurchaseOrderLine, PurchaseInvoice, PurchaseReturn
from .serializers import (
    VendorSerializer,
    PurchaseOrderSerializer, PurchaseOrderCreateSerializer,
    PurchaseInvoiceSerializer,
    PurchaseReturnSerializer,
)


class VendorViewSet(viewsets.ModelViewSet):
    """
    GET    /api/purchase/vendors/       — list vendors
    POST   /api/purchase/vendors/       — create vendor
    GET    /api/purchase/vendors/{id}/  — retrieve
    PUT    /api/purchase/vendors/{id}/  — update
    DELETE /api/purchase/vendors/{id}/  — delete
    """
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['name', 'email', 'phone', 'gstin']
    filterset_fields = ['company', 'is_active']

    def get_queryset(self):
        qs = super().get_queryset()
        company_id = self.request.query_params.get('company')
        if company_id:
            qs = qs.filter(company_id=company_id)
        return qs


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    """
    GET    /api/purchase/orders/                     — list POs
    POST   /api/purchase/orders/                     — create PO with lines
    GET    /api/purchase/orders/{id}/                — retrieve with lines
    PUT    /api/purchase/orders/{id}/                — update
    DELETE /api/purchase/orders/{id}/                — delete
    POST   /api/purchase/orders/{id}/receive/        — mark items as received
    POST   /api/purchase/orders/{id}/change_status/  — update status
    POST   /api/purchase/orders/{id}/create_invoice/ — generate purchase invoice from PO
    """
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['po_number', 'vendor_name', 'vendor__name']
    filterset_fields = ['company', 'status']

    def get_queryset(self):
        qs = PurchaseOrder.objects.all().select_related(
            'company', 'vendor'
        ).prefetch_related('lines')
        company_id = self.request.query_params.get('company')
        if company_id:
            qs = qs.filter(company_id=company_id)
        return qs.order_by('-date', '-id')

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return PurchaseOrderCreateSerializer
        return PurchaseOrderSerializer

    @action(detail=True, methods=['post'])
    def receive(self, request, pk=None):
        """
        Mark items as received.
        Body: [{"line_id": 1, "received_quantity": 5}, ...]
        """
        po = self.get_object()
        receipts = request.data.get('receipts', [])
        for receipt in receipts:
            try:
                line = po.lines.get(id=receipt['line_id'])
                qty = float(receipt.get('received_quantity', 0))
                line.received_quantity = min(
                    float(line.quantity),
                    float(line.received_quantity) + qty
                )
                line.save(update_fields=['received_quantity'])
            except PurchaseOrderLine.DoesNotExist:
                pass

        # Update PO status
        all_lines = po.lines.all()
        if all(l.received_quantity >= l.quantity for l in all_lines):
            po.status = 'Received'
        else:
            po.status = 'Partial'
        po.save(update_fields=['status'])

        return Response(PurchaseOrderSerializer(po).data)

    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        po = self.get_object()
        new_status = request.data.get('status')
        valid = [s[0] for s in PurchaseOrder.STATUS_CHOICES]
        if new_status not in valid:
            return Response(
                {'error': f'Invalid status. Choose from: {valid}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        po.status = new_status
        po.save(update_fields=['status'])
        return Response({'id': po.id, 'status': po.status})

    @action(detail=True, methods=['post'])
    def create_invoice(self, request, pk=None):
        """Generate a purchase invoice from this PO"""
        po = self.get_object()
        count = PurchaseInvoice.objects.filter(company=po.company).count() + 1
        inv_number = f'PINV-{po.company_id}-{count:04d}'

        invoice = PurchaseInvoice.objects.create(
            company=po.company,
            invoice_number=inv_number,
            date=po.date,
            purchase_order=po,
            vendor=po.vendor,
            vendor_name=po.vendor_name,
            subtotal=po.subtotal,
            total_gst=po.total_gst,
            total_amount=po.total_amount,
            status='Pending',
        )
        return Response(
            PurchaseInvoiceSerializer(invoice).data,
            status=status.HTTP_201_CREATED
        )


class PurchaseInvoiceViewSet(viewsets.ModelViewSet):
    """
    GET    /api/purchase/invoices/            — list purchase invoices
    POST   /api/purchase/invoices/            — create
    GET    /api/purchase/invoices/{id}/       — retrieve
    PUT    /api/purchase/invoices/{id}/       — update
    DELETE /api/purchase/invoices/{id}/       — delete
    POST   /api/purchase/invoices/{id}/pay/   — record payment
    """
    queryset = PurchaseInvoice.objects.all().select_related('company', 'vendor', 'purchase_order')
    serializer_class = PurchaseInvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['invoice_number', 'vendor_invoice_number', 'vendor_name']
    filterset_fields = ['company', 'status']

    def get_queryset(self):
        qs = super().get_queryset()
        company_id = self.request.query_params.get('company')
        if company_id:
            qs = qs.filter(company_id=company_id)
        return qs.order_by('-date', '-id')

    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        """Record a payment against this invoice"""
        invoice = self.get_object()
        amount = float(request.data.get('amount', 0))
        invoice.paid_amount = min(
            float(invoice.total_amount),
            float(invoice.paid_amount) + amount
        )
        if invoice.paid_amount >= float(invoice.total_amount):
            invoice.status = 'Paid'
        else:
            invoice.status = 'Partial'
        invoice.save(update_fields=['paid_amount', 'status'])
        return Response(PurchaseInvoiceSerializer(invoice).data)


class PurchaseReturnViewSet(viewsets.ModelViewSet):
    """
    GET    /api/purchase/returns/       — list returns
    POST   /api/purchase/returns/       — create return
    GET    /api/purchase/returns/{id}/  — retrieve
    DELETE /api/purchase/returns/{id}/  — delete
    """
    queryset = PurchaseReturn.objects.all().select_related('company', 'vendor')
    serializer_class = PurchaseReturnSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['company']

    def get_queryset(self):
        qs = super().get_queryset()
        company_id = self.request.query_params.get('company')
        if company_id:
            qs = qs.filter(company_id=company_id)
        return qs.order_by('-date', '-id')
