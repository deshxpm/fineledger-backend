from rest_framework import serializers
from .models import Category, Product, StockMovement


class CategorySerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ('id', 'company', 'name', 'description', 'parent', 'parent_name', 'product_count', 'created_at')
        read_only_fields = ('created_at',)

    def get_product_count(self, obj):
        return obj.products.count()


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    stock_value = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = Product
        fields = (
            'id', 'company', 'sku', 'name', 'description',
            'category', 'category_name', 'unit',
            'cost_price', 'selling_price', 'mrp', 'gst_rate', 'hsn_code',
            'stock_quantity', 'min_stock_level', 'max_stock_level', 'reorder_quantity',
            'is_low_stock', 'stock_value',
            'is_active', 'is_taxable', 'track_inventory',
            'created_at', 'updated_at'
        )
        read_only_fields = ('created_at', 'updated_at')


class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)

    class Meta:
        model = StockMovement
        fields = (
            'id', 'company', 'product', 'product_name', 'product_sku',
            'movement_type', 'quantity', 'balance_after',
            'unit_cost', 'reference', 'notes', 'date',
            'created_by', 'created_at'
        )
        read_only_fields = ('created_at', 'balance_after')


class StockAdjustSerializer(serializers.Serializer):
    """Used for manual stock adjustments"""
    movement_type = serializers.ChoiceField(choices=['IN', 'OUT', 'ADJUST'])
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=0)
    unit_cost = serializers.DecimalField(max_digits=15, decimal_places=2, required=False, default=0)
    reference = serializers.CharField(max_length=50, required=False, default='')
    notes = serializers.CharField(required=False, default='')
    date = serializers.DateField()
