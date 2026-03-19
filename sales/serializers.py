from rest_framework import serializers
from .models import Customer, SalesDocument, SalesDocumentLine


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = ('created_at',)


class SalesDocumentLineSerializer(serializers.ModelSerializer):
    line_total = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    gst_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    taxable_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    line_total_with_gst = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = SalesDocumentLine
        fields = (
            'id', 'document', 'line_number', 'product_name', 'product_sku',
            'description', 'quantity', 'unit', 'rate', 'gst_rate',
            'discount_pct', 'taxable_amount', 'gst_amount',
            'line_total', 'line_total_with_gst'
        )
        read_only_fields = ('document',)


class SalesDocumentSerializer(serializers.ModelSerializer):
    lines = SalesDocumentLineSerializer(many=True, read_only=True)
    customer_display = serializers.SerializerMethodField()

    class Meta:
        model = SalesDocument
        fields = (
            'id', 'company', 'doc_type', 'doc_number', 'date', 'due_date',
            'customer', 'customer_name', 'customer_display',
            'billing_address', 'shipping_address',
            'status', 'gst_type', 'subtotal', 'total_gst',
            'discount', 'total_amount', 'notes', 'terms',
            'parent_document', 'lines', 'created_at', 'updated_at'
        )
        read_only_fields = ('created_at', 'updated_at', 'subtotal', 'total_gst', 'total_amount')

    def get_customer_display(self, obj):
        if obj.customer:
            return obj.customer.name
        return obj.customer_name


class SalesDocumentCreateSerializer(serializers.ModelSerializer):
    """Handles creation with inline lines"""
    lines = SalesDocumentLineSerializer(many=True)

    class Meta:
        model = SalesDocument
        fields = (
            'company', 'doc_type', 'doc_number', 'date', 'due_date',
            'customer', 'customer_name', 'billing_address', 'shipping_address',
            'status', 'gst_type', 'discount', 'notes', 'terms',
            'parent_document', 'lines'
        )

    def create(self, validated_data):
        lines_data = validated_data.pop('lines', [])
        doc = SalesDocument.objects.create(**validated_data)
        for i, line_data in enumerate(lines_data, start=1):
            line_data['line_number'] = i
            SalesDocumentLine.objects.create(document=doc, **line_data)
        doc.recalculate_totals()
        return doc

    def update(self, instance, validated_data):
        lines_data = validated_data.pop('lines', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if lines_data is not None:
            instance.lines.all().delete()
            for i, line_data in enumerate(lines_data, start=1):
                line_data['line_number'] = i
                SalesDocumentLine.objects.create(document=instance, **line_data)
            instance.recalculate_totals()
        return instance
