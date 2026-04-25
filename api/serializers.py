from rest_framework import serializers
from core.models import Branch
from inventory.models import Product, BranchStock, StockTransfer, StockTransferItem
from sales.models import Sale, SaleItem, Payment, Customer


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ['id', 'name', 'code', 'address', 'phone', 'email', 'is_active']


class BranchStockSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.name', read_only=True)

    class Meta:
        model = BranchStock
        fields = ['branch', 'branch_name', 'quantity']


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    branch_stocks = BranchStockSerializer(many=True, read_only=True)
    stock_in_branch = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'category', 'category_name',
            'description', 'price', 'cost', 'min_stock',
            'is_active', 'branch_stocks', 'stock_in_branch'
        ]

    def get_stock_in_branch(self, obj):
        branch_id = self.context.get('branch_id')
        if branch_id:
            try:
                return obj.branch_stocks.get(branch_id=branch_id).quantity
            except BranchStock.DoesNotExist:
                return 0
        return None


class SaleItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)


class CreateSaleSerializer(serializers.Serializer):
    branch_id = serializers.IntegerField()
    customer_id = serializers.IntegerField(required=False, allow_null=True)
    items = SaleItemSerializer(many=True)
    discount = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = serializers.CharField(required=False, allow_blank=True)
    payment_method = serializers.ChoiceField(choices=['efectivo', 'tarjeta', 'transferencia'])
    payment_amount = serializers.DecimalField(max_digits=10, decimal_places=2)


class StockTransferItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = StockTransferItem
        fields = ['id', 'product', 'product_name', 'quantity', 'quantity_received', 'notes']


class StockTransferSerializer(serializers.ModelSerializer):
    items = StockTransferItemSerializer(many=True, read_only=True)
    origin_branch_name = serializers.CharField(source='origin_branch.name', read_only=True)
    destination_branch_name = serializers.CharField(source='destination_branch.name', read_only=True)

    class Meta:
        model = StockTransfer
        fields = [
            'id', 'transfer_number', 'origin_branch', 'origin_branch_name',
            'destination_branch', 'destination_branch_name',
            'status', 'notes', 'created_at', 'completed_at', 'items'
        ]


class CreateTransferSerializer(serializers.Serializer):
    origin_branch = serializers.IntegerField()
    destination_branch = serializers.IntegerField()
    notes = serializers.CharField(required=False, allow_blank=True)
    items = serializers.ListField(
        child=serializers.DictField()
    )
