from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Count
from .models import Category, Product, StockMovement
from .serializers import (
    CategorySerializer, ProductSerializer,
    StockMovementSerializer, StockAdjustSerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    GET    /api/inventory/categories/       — list categories
    POST   /api/inventory/categories/       — create
    GET    /api/inventory/categories/{id}/  — retrieve
    PUT    /api/inventory/categories/{id}/  — update
    DELETE /api/inventory/categories/{id}/  — delete
    """
    queryset = Category.objects.all().select_related('parent')
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['name']
    filterset_fields = ['company']

    def get_queryset(self):
        qs = super().get_queryset()
        company_id = self.request.query_params.get('company')
        if company_id:
            qs = qs.filter(company_id=company_id)
        return qs


class ProductViewSet(viewsets.ModelViewSet):
    """
    GET    /api/inventory/products/                    — list all products
    POST   /api/inventory/products/                    — create product
    GET    /api/inventory/products/{id}/               — retrieve
    PUT    /api/inventory/products/{id}/               — update
    DELETE /api/inventory/products/{id}/               — delete
    GET    /api/inventory/products/low_stock/          — products below min level
    GET    /api/inventory/products/stock_valuation/    — total inventory value
    POST   /api/inventory/products/{id}/adjust_stock/  — manual stock adjustment
    GET    /api/inventory/products/{id}/movements/     — stock movement history
    """
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['name', 'sku', 'hsn_code']
    filterset_fields = ['company', 'category', 'is_active']

    def get_queryset(self):
        qs = Product.objects.all().select_related('category', 'company')
        company_id = self.request.query_params.get('company')
        category_id = self.request.query_params.get('category')
        low_stock = self.request.query_params.get('low_stock')

        if company_id:
            qs = qs.filter(company_id=company_id)
        if category_id:
            qs = qs.filter(category_id=category_id)
        if low_stock == 'true':
            qs = qs.filter(stock_quantity__lt=F('min_stock_level'))
        return qs.order_by('name')

    def get_serializer_class(self):
        return ProductSerializer

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Products where current stock < minimum stock level"""
        company_id = request.query_params.get('company')
        qs = Product.objects.filter(stock_quantity__lt=F('min_stock_level'))
        if company_id:
            qs = qs.filter(company_id=company_id)
        return Response(ProductSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'])
    def stock_valuation(self, request):
        """Summary of total stock value by category"""
        company_id = request.query_params.get('company')
        qs = Product.objects.all()
        if company_id:
            qs = qs.filter(company_id=company_id)

        # Per-category breakdown
        by_category = (
            qs.values('category__name')
            .annotate(
                product_count=Count('id'),
                total_qty=Sum('stock_quantity'),
            )
            .order_by('category__name')
        )

        # Compute stock values manually (DecimalField * DecimalField not supported in all DBs via annotate)
        total_value = sum(float(p.stock_value) for p in qs)
        low_count = qs.filter(stock_quantity__lt=F('min_stock_level')).count()

        return Response({
            'total_stock_value': round(total_value, 2),
            'total_products': qs.count(),
            'low_stock_count': low_count,
            'by_category': list(by_category),
        })

    @action(detail=True, methods=['post'])
    def adjust_stock(self, request, pk=None):
        """
        Manually adjust stock for a product.
        Body: { movement_type, quantity, unit_cost, reference, notes, date }
        """
        product = self.get_object()
        serializer = StockAdjustSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        qty = float(data['quantity'])
        move_type = data['movement_type']

        if move_type == 'IN':
            product.stock_quantity = float(product.stock_quantity) + qty
        elif move_type == 'OUT':
            if float(product.stock_quantity) < qty:
                return Response(
                    {'error': f'Insufficient stock. Available: {product.stock_quantity}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            product.stock_quantity = float(product.stock_quantity) - qty
        elif move_type == 'ADJUST':
            product.stock_quantity = qty  # Set absolute value

        product.save(update_fields=['stock_quantity'])

        # Record movement
        movement = StockMovement.objects.create(
            company=product.company,
            product=product,
            movement_type=move_type,
            quantity=data['quantity'],
            balance_after=product.stock_quantity,
            unit_cost=data.get('unit_cost', 0),
            reference=data.get('reference', ''),
            notes=data.get('notes', ''),
            date=data['date'],
            created_by=request.user,
        )

        return Response({
            'product': ProductSerializer(product).data,
            'movement': StockMovementSerializer(movement).data,
        })

    @action(detail=True, methods=['get'])
    def movements(self, request, pk=None):
        """Full stock movement history for this product"""
        product = self.get_object()
        movements = StockMovement.objects.filter(
            product=product
        ).order_by('-date', '-id')
        return Response(StockMovementSerializer(movements, many=True).data)


class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/inventory/movements/        — list all movements (read-only)
    GET /api/inventory/movements/{id}/   — retrieve single movement

    Use POST /api/inventory/products/{id}/adjust_stock/ to create movements.
    """
    queryset = StockMovement.objects.all().select_related('product', 'company')
    serializer_class = StockMovementSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['product__name', 'product__sku', 'reference']
    filterset_fields = ['company', 'movement_type', 'product']

    def get_queryset(self):
        qs = super().get_queryset()
        company_id = self.request.query_params.get('company')
        product_id = self.request.query_params.get('product')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if company_id:
            qs = qs.filter(company_id=company_id)
        if product_id:
            qs = qs.filter(product_id=product_id)
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        return qs.order_by('-date', '-id')
