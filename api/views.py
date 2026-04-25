from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
import decimal

from core.models import Branch
from inventory.models import Product, BranchStock, StockMovement, StockTransfer, StockTransferItem
from sales.models import Sale, SaleItem, Payment
from .serializers import (
    ProductSerializer, BranchSerializer, StockTransferSerializer,
    CreateSaleSerializer, CreateTransferSerializer
)


def success(data=None, message=''):
    return Response({'success': True, 'data': data, 'message': message})


def error(message, status_code=400):
    return Response({'success': False, 'data': None, 'message': message}, status=status_code)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def product_list(request):
    user = request.user
    branch_id = request.GET.get('branch')

    if not user.is_superadmin:
        branch_id = user.branch.pk if user.branch else None

    qs = Product.objects.filter(is_active=True).select_related('category').prefetch_related('branch_stocks__branch')
    serializer = ProductSerializer(qs, many=True, context={'branch_id': branch_id, 'request': request})
    return success(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def product_detail(request, pk):
    try:
        product = Product.objects.select_related('category').prefetch_related('branch_stocks__branch').get(pk=pk)
    except Product.DoesNotExist:
        return error('Producto no encontrado.', 404)
    serializer = ProductSerializer(product, context={'request': request})
    return success(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_sale(request):
    serializer = CreateSaleSerializer(data=request.data)
    if not serializer.is_valid():
        return error(str(serializer.errors))

    data = serializer.validated_data
    user = request.user

    if not user.is_superadmin:
        branch_id = user.branch.pk if user.branch else None
    else:
        branch_id = data['branch_id']

    try:
        branch = Branch.objects.get(pk=branch_id, is_active=True)
    except Branch.DoesNotExist:
        return error('Sucursal no válida.')

    from core.models import SystemSettings
    TAX_RATE = SystemSettings.get_tax_rate()

    try:
        with transaction.atomic():
            sale = Sale.objects.create(
                branch=branch, customer_id=data.get('customer_id'),
                seller=user, discount=data.get('discount', 0),
                notes=data.get('notes', ''), status='completada',
                subtotal=0, tax=0, total=0,
            )
            for item_data in data['items']:
                product = Product.objects.select_for_update().get(pk=item_data['product_id'])
                qty = item_data['quantity']
                stock = BranchStock.objects.select_for_update().get(product=product, branch=branch)
                if stock.quantity < qty:
                    raise ValueError(f'Stock insuficiente de "{product.name}"')
                SaleItem.objects.create(
                    sale=sale, product=product, quantity=qty,
                    unit_price=item_data['unit_price'],
                    discount=item_data.get('discount', 0),
                    subtotal=(item_data['unit_price'] * qty) - item_data.get('discount', 0),
                )
                stock.quantity -= qty
                stock.save()
                StockMovement.objects.create(
                    product=product, branch=branch, movement_type='salida',
                    quantity=-qty, reason=f'Venta {sale.invoice_number}', created_by=user
                )
            Payment.objects.create(
                sale=sale, method=data['payment_method'], amount=data['payment_amount']
            )
            sale.refresh_from_db()
    except (ValueError, Product.DoesNotExist, BranchStock.DoesNotExist) as e:
        return error(str(e))

    return success({'invoice_number': sale.invoice_number, 'sale_id': sale.pk}, 'Venta creada.')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    user = request.user
    today = timezone.now().date()
    month_start = today.replace(day=1)
    branch_id = request.GET.get('branch')

    sale_filter = Q(status='completada')
    stock_filter = Q()

    if not user.is_superadmin:
        sale_filter &= Q(branch=user.branch)
        stock_filter = Q(branch=user.branch)
    elif branch_id and branch_id != 'all':
        try:
            branch = Branch.objects.get(pk=branch_id)
            sale_filter &= Q(branch=branch)
            stock_filter = Q(branch=branch)
        except Branch.DoesNotExist:
            pass

    sales_today = Sale.objects.filter(sale_filter, created_at__date=today)
    monthly = Sale.objects.filter(sale_filter, created_at__date__gte=month_start)

    low_stock = BranchStock.objects.filter(
        stock_filter, quantity__lte=F('product__min_stock')
    ).count()

    data = {
        'sales_today': sales_today.count(),
        'revenue_today': float(sales_today.aggregate(t=Sum('total'))['t'] or 0),
        'monthly_revenue': float(monthly.aggregate(t=Sum('total'))['t'] or 0),
        'low_stock_count': low_stock,
        'customers_new': 0,
    }
    return success(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def low_stock(request):
    user = request.user
    branch_id = request.GET.get('branch')

    qs = BranchStock.objects.filter(quantity__lte=F('product__min_stock')).select_related('product', 'branch')

    if not user.is_superadmin:
        qs = qs.filter(branch=user.branch)
    elif branch_id:
        qs = qs.filter(branch_id=branch_id)

    data = [{
        'product': bs.product.name,
        'sku': bs.product.sku,
        'branch': bs.branch.name,
        'quantity': bs.quantity,
        'min_stock': bs.product.min_stock,
    } for bs in qs]
    return success(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def branch_list(request):
    branches = Branch.objects.filter(is_active=True)
    serializer = BranchSerializer(branches, many=True)
    return success(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def transfer_create(request):
    serializer = CreateTransferSerializer(data=request.data)
    if not serializer.is_valid():
        return error(str(serializer.errors))

    data = serializer.validated_data
    try:
        origin = Branch.objects.get(pk=data['origin_branch'], is_active=True)
        destination = Branch.objects.get(pk=data['destination_branch'], is_active=True)
    except Branch.DoesNotExist:
        return error('Sucursal no válida.')

    if origin == destination:
        return error('Las sucursales deben ser distintas.')

    try:
        with transaction.atomic():
            transfer = StockTransfer.objects.create(
                origin_branch=origin, destination_branch=destination,
                notes=data.get('notes', ''), created_by=request.user, status='en_transito'
            )
            for item_data in data['items']:
                product = Product.objects.select_for_update().get(pk=item_data['product_id'])
                qty = int(item_data['quantity'])
                stock = BranchStock.objects.select_for_update().get(product=product, branch=origin)
                if stock.quantity < qty:
                    raise ValueError(f'Stock insuficiente de {product.name}')
                stock.quantity -= qty
                stock.save()
                StockTransferItem.objects.create(transfer=transfer, product=product, quantity=qty)
                StockMovement.objects.create(
                    product=product, branch=origin, movement_type='transferencia_salida',
                    quantity=-qty, reason=f'Transferencia {transfer.transfer_number}',
                    reference=transfer, created_by=request.user
                )
    except (ValueError, Product.DoesNotExist, BranchStock.DoesNotExist) as e:
        return error(str(e))

    return success({'transfer_number': transfer.transfer_number, 'id': transfer.pk})


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def transfer_complete(request, pk):
    try:
        transfer = StockTransfer.objects.get(pk=pk)
    except StockTransfer.DoesNotExist:
        return error('Transferencia no encontrada.', 404)

    if transfer.status != 'en_transito':
        return error('La transferencia no está en tránsito.')

    items_data = request.data.get('items', [])
    try:
        with transaction.atomic():
            for item_data in items_data:
                item = StockTransferItem.objects.get(pk=item_data['item_id'], transfer=transfer)
                qty_received = int(item_data['quantity_received'])
                item.quantity_received = qty_received
                item.save()
                stock, _ = BranchStock.objects.select_for_update().get_or_create(
                    product=item.product, branch=transfer.destination_branch,
                    defaults={'quantity': 0}
                )
                stock.quantity += qty_received
                stock.save()
                StockMovement.objects.create(
                    product=item.product, branch=transfer.destination_branch,
                    movement_type='transferencia_entrada', quantity=qty_received,
                    reason=f'Recepción {transfer.transfer_number}',
                    reference=transfer, created_by=request.user
                )
            transfer.status = 'completada'
            transfer.completed_at = timezone.now()
            transfer.save()
    except Exception as e:
        return error(str(e))

    return success({'transfer_number': transfer.transfer_number})
