from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count
from .models import Customer, SalesDocument, SalesDocumentLine
from .serializers import (
    CustomerSerializer,
    SalesDocumentSerializer,
    SalesDocumentCreateSerializer,
    SalesDocumentLineSerializer,
)


class CustomerViewSet(viewsets.ModelViewSet):
    """
    GET    /api/sales/customers/       — list customers
    POST   /api/sales/customers/       — create customer
    GET    /api/sales/customers/{id}/  — retrieve
    PUT    /api/sales/customers/{id}/  — update
    DELETE /api/sales/customers/{id}/  — delete
    GET    /api/sales/customers/{id}/documents/ — all sales docs for this customer
    """
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['name', 'email', 'phone', 'gstin']
    filterset_fields = ['company', 'is_active']

    def get_queryset(self):
        qs = super().get_queryset()
        company_id = self.request.query_params.get('company')
        if company_id:
            qs = qs.filter(company_id=company_id)
        return qs

    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        customer = self.get_object()
        docs = SalesDocument.objects.filter(customer=customer).order_by('-date')
        return Response(SalesDocumentSerializer(docs, many=True).data)

    @action(detail=True, methods=['get'])
    def outstanding(self, request, pk=None):
        """Unpaid / overdue invoices for this customer"""
        customer = self.get_object()
        docs = SalesDocument.objects.filter(
            customer=customer,
            doc_type='Invoice',
            status__in=['Pending', 'Overdue']
        )
        total = docs.aggregate(total=Sum('total_amount'))['total'] or 0
        return Response({
            'customer': customer.name,
            'outstanding_amount': total,
            'invoices': SalesDocumentSerializer(docs, many=True).data
        })


class SalesDocumentViewSet(viewsets.ModelViewSet):
    """
    GET    /api/sales/documents/                       — list (filter by doc_type, status, company)
    POST   /api/sales/documents/                       — create with lines
    GET    /api/sales/documents/{id}/                  — retrieve with lines
    PUT    /api/sales/documents/{id}/                  — update (replaces all lines)
    PATCH  /api/sales/documents/{id}/                  — partial update
    DELETE /api/sales/documents/{id}/                  — delete
    POST   /api/sales/documents/{id}/convert/          — convert to next stage
    POST   /api/sales/documents/{id}/change_status/    — change status
    GET    /api/sales/documents/pipeline_summary/      — counts per stage
    """
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['doc_number', 'customer_name', 'customer__name']
    filterset_fields = ['company', 'doc_type', 'status']

    def get_queryset(self):
        qs = SalesDocument.objects.all().select_related(
            'company', 'customer', 'parent_document'
        ).prefetch_related('lines')
        company_id = self.request.query_params.get('company')
        doc_type = self.request.query_params.get('doc_type')
        status_filter = self.request.query_params.get('status')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')

        if company_id:
            qs = qs.filter(company_id=company_id)
        if doc_type:
            qs = qs.filter(doc_type=doc_type)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        return qs.order_by('-date', '-id')

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return SalesDocumentCreateSerializer
        return SalesDocumentSerializer

    # ── Pipeline stage conversion ──────────────────────────────────────────
    NEXT_STAGE = {
        'Quotation': 'Proforma',
        'Proforma': 'Order',
        'Order': 'Challan',
        'Challan': 'Invoice',
    }
    NEXT_STATUS = {
        'Quotation': 'Converted',
        'Proforma': 'Approved',
        'Order': 'Confirmed',
        'Challan': 'Dispatched',
    }

    @action(detail=True, methods=['post'])
    def convert(self, request, pk=None):
        """Convert document to the next pipeline stage"""
        doc = self.get_object()
        next_type = self.NEXT_STAGE.get(doc.doc_type)
        if not next_type:
            return Response(
                {'error': 'Invoices cannot be converted further.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Build new document number
        count = SalesDocument.objects.filter(
            company=doc.company, doc_type=next_type
        ).count() + 1
        prefix_map = {
            'Proforma': 'PI', 'Order': 'SO', 'Challan': 'DC', 'Invoice': 'INV'
        }
        prefix = prefix_map.get(next_type, next_type[:2].upper())
        new_number = f'{prefix}-{doc.company_id}-{count:04d}'

        new_doc = SalesDocument.objects.create(
            company=doc.company,
            doc_type=next_type,
            doc_number=new_number,
            date=doc.date,
            due_date=doc.due_date,
            customer=doc.customer,
            customer_name=doc.customer_name,
            billing_address=doc.billing_address,
            shipping_address=doc.shipping_address,
            status='Draft',
            gst_type=doc.gst_type,
            discount=doc.discount,
            notes=doc.notes,
            terms=doc.terms,
            parent_document=doc,
        )

        # Copy lines
        for line in doc.lines.all():
            SalesDocumentLine.objects.create(
                document=new_doc,
                line_number=line.line_number,
                product_name=line.product_name,
                product_sku=line.product_sku,
                description=line.description,
                quantity=line.quantity,
                unit=line.unit,
                rate=line.rate,
                gst_rate=line.gst_rate,
                discount_pct=line.discount_pct,
            )
        new_doc.recalculate_totals()

        # Mark original as converted
        doc.status = self.NEXT_STATUS.get(doc.doc_type, 'Converted')
        doc.save(update_fields=['status'])

        return Response(
            SalesDocumentSerializer(new_doc).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        doc = self.get_object()
        new_status = request.data.get('status')
        valid = [s[0] for s in SalesDocument.STATUS_CHOICES]
        if new_status not in valid:
            return Response(
                {'error': f'Invalid status. Choose from: {valid}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        doc.status = new_status
        doc.save(update_fields=['status'])
        return Response({'id': doc.id, 'status': doc.status})

    @action(detail=False, methods=['get'])
    def pipeline_summary(self, request):
        """Returns count + amount per pipeline stage"""
        company_id = request.query_params.get('company')
        qs = SalesDocument.objects.all()
        if company_id:
            qs = qs.filter(company_id=company_id)

        summary = qs.values('doc_type').annotate(
            count=Count('id'),
            total_amount=Sum('total_amount')
        ).order_by('doc_type')
        return Response(list(summary))
