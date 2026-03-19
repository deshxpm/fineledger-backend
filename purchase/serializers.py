from rest_framework import serializers
from .models import Vendor, PurchaseOrder, PurchaseOrderLine, PurchaseInvoice, PurchaseReturn


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = '__all__'
        read_only_fields = ('created_at',)


class PurchaseOrderLineSerializer(serializers.ModelSerializer):
    taxable_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    gst_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    line_total = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    pending_quantity = serializers.DecimalField(max_digits=10, decimal_places=3, read_only=True)

    class Meta:
        model = PurchaseOrderLine
        fields = (
            'id', 'purchase_order', 'line_number', 'product_name', 'product_sku',
            'quantity', 'received_quantity', 'pending_quantity',
            'unit', 'rate', 'gst_rate',
            'taxable_amount', 'gst_amount', 'line_total'
        )
        read_only_fields = ('purchase_order', 'received_quantity')


class PurchaseOrderSerializer(serializers.ModelSerializer):
    lines = PurchaseOrderLineSerializer(many=True, read_only=True)
    vendor_display = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseOrder
        fields = (
            'id', 'company', 'po_number', 'date', 'expected_delivery',
            'vendor', 'vendor_name', 'vendor_display', 'status',
            'subtotal', 'total_gst', 'total_amount',
            'notes', 'item_count', 'lines', 'created_at', 'updated_at'
        )
        read_only_fields = ('created_at', 'updated_at', 'subtotal', 'total_gst', 'total_amount')

    def get_vendor_display(self, obj):
        return obj.vendor.name if obj.vendor else obj.vendor_name

    def get_item_count(self, obj):
        return obj.lines.count()


class PurchaseOrderCreateSerializer(serializers.ModelSerializer):
    lines = PurchaseOrderLineSerializer(many=True)

    class Meta:
        model = PurchaseOrder
        fields = (
            'company', 'po_number', 'date', 'expected_delivery',
            'vendor', 'vendor_name', 'status', 'notes', 'lines'
        )

    def create(self, validated_data):
        lines_data = validated_data.pop('lines', [])
        po = PurchaseOrder.objects.create(**validated_data)
        for i, line_data in enumerate(lines_data, start=1):
            line_data['line_number'] = i
            PurchaseOrderLine.objects.create(purchase_order=po, **line_data)
        po.recalculate_totals()
        return po

    def update(self, instance, validated_data):
        lines_data = validated_data.pop('lines', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if lines_data is not None:
            instance.lines.all().delete()
            for i, line_data in enumerate(lines_data, start=1):
                line_data['line_number'] = i
                PurchaseOrderLine.objects.create(purchase_order=instance, **line_data)
            instance.recalculate_totals()
        return instance


class PurchaseInvoiceSerializer(serializers.ModelSerializer):
    balance_due = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    vendor_display = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseInvoice
        fields = (
            'id', 'company', 'invoice_number', 'vendor_invoice_number',
            'date', 'due_date', 'purchase_order', 'vendor', 'vendor_name',
            'vendor_display', 'subtotal', 'total_gst', 'total_amount',
            'paid_amount', 'balance_due', 'status', 'notes',
            'created_at', 'updated_at'
        )
        read_only_fields = ('created_at', 'updated_at')

    def get_vendor_display(self, obj):
        return obj.vendor.name if obj.vendor else obj.vendor_name


class PurchaseReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseReturn
        fields = '__all__'
        read_only_fields = ('created_at',)
