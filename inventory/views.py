from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.db.models import Q, F, Sum, OuterRef, Subquery
from django.core.paginator import Paginator
from django.utils import timezone
import csv

from core.mixins import BranchAccessMixin
from core.models import Branch
from .models import (
    Category, Supplier, Product, BranchStock,
    StockMovement, StockTransfer, StockTransferItem
)
from .forms import ProductForm, CategoryForm, SupplierForm, StockAdjustForm, StockTransferForm


def _get_active_branch(request):
    user = request.user
    if not user.is_superadmin:
        return user.branch
    branch_id = request.session.get('active_branch_id')
    if branch_id:
        try:
            return Branch.objects.get(pk=branch_id, is_active=True)
        except Branch.DoesNotExist:
            pass
    return None


@login_required
def product_list(request):
    user = request.user
    active_branch = _get_active_branch(request)
    q = request.GET.get('q', '')
    category_id = request.GET.get('category', '')

    # Only show products that exist in the active branch
    stock_subq = BranchStock.objects.filter(
        product=OuterRef('pk'), branch=active_branch
    ).values('quantity')[:1]

    qs = (
        Product.objects
        .filter(branch_stocks__branch=active_branch)
        .select_related('category', 'supplier')
        .annotate(branch_quantity=Subquery(stock_subq))
        .distinct()
    )

    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(sku__icontains=q))
    if category_id:
        qs = qs.filter(category_id=category_id)

    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get('page'))
    categories = Category.objects.all()

    return render(request, 'inventory/product_list.html', {
        'page_obj': page, 'categories': categories,
        'active_branch': active_branch, 'q': q, 'category_id': category_id,
    })


@login_required
def product_create(request):
    if request.user.is_cashier:
        return JsonResponse({'success': False, 'message': 'Sin permisos'}, status=403)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            active_branch = _get_active_branch(request)
            if active_branch:
                initial_stock = max(0, int(request.POST.get('initial_stock', 0) or 0))
                BranchStock.objects.get_or_create(
                    product=product, branch=active_branch,
                    defaults={'quantity': initial_stock}
                )
            return JsonResponse({'success': True, 'id': product.pk})
        return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False})


@login_required
def product_update(request, pk):
    if request.user.is_cashier:
        return JsonResponse({'success': False, 'message': 'Sin permisos'}, status=403)
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors})
    data = {
        'id': product.pk, 'name': product.name, 'sku': product.sku,
        'category': product.category_id, 'supplier': product.supplier_id,
        'description': product.description, 'price': str(product.price),
        'cost': str(product.cost), 'min_stock': product.min_stock,
        'is_active': product.is_active,
    }
    return JsonResponse({'success': True, 'data': data})


@login_required
def product_delete(request, pk):
    if request.user.is_cashier:
        return JsonResponse({'success': False, 'message': 'Sin permisos'}, status=403)
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=pk)
        from sales.models import SaleItem
        if SaleItem.objects.filter(product=product).exists():
            return JsonResponse({
                'success': False,
                'message': f'No se puede eliminar "{product.name}": tiene ventas registradas. Puedes desactivarlo desde Editar.'
            })
        product.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


@login_required
def stock_adjust(request, pk):
    if request.user.is_cashier:
        return JsonResponse({'success': False, 'message': 'Sin permisos'}, status=403)
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = StockAdjustForm(request.POST)
        active_branch = _get_active_branch(request)
        form.data = form.data.copy()
        form.data['branch'] = active_branch.pk if active_branch else ''
        if form.is_valid():
            branch = form.cleaned_data['branch']
            quantity = form.cleaned_data['quantity']
            reason = form.cleaned_data.get('reason', '')
            with transaction.atomic():
                stock, _ = BranchStock.objects.select_for_update().get_or_create(
                    product=product, branch=branch, defaults={'quantity': 0}
                )
                stock.quantity = quantity
                stock.save()
                StockMovement.objects.create(
                    product=product, branch=branch,
                    movement_type='ajuste', quantity=quantity,
                    reason=reason, created_by=request.user
                )
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False})


@login_required
def product_export_csv(request):
    user = request.user
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="productos.csv"'
    response.write('\ufeff')

    writer = csv.writer(response)
    if user.is_superadmin:
        branches = list(Branch.objects.filter(is_active=True))
        header = ['SKU', 'Nombre', 'Categoría', 'Precio', 'Costo'] + [b.name for b in branches]
        writer.writerow(header)
        for product in Product.objects.select_related('category').prefetch_related('branch_stocks__branch'):
            row = [product.sku, product.name,
                   product.category.name if product.category else '',
                   product.price, product.cost]
            for branch in branches:
                row.append(product.get_stock_for_branch(branch))
            writer.writerow(row)
    else:
        writer.writerow(['SKU', 'Nombre', 'Categoría', 'Precio', 'Stock'])
        branch = user.branch
        for bs in BranchStock.objects.filter(branch=branch).select_related('product__category'):
            writer.writerow([
                bs.product.sku, bs.product.name,
                bs.product.category.name if bs.product.category else '',
                bs.product.price, bs.quantity,
            ])
    return response


@login_required
def transfer_list(request):
    user = request.user
    qs = StockTransfer.objects.select_related(
        'origin_branch', 'destination_branch', 'created_by'
    ).prefetch_related('items__product')

    if not user.is_superadmin:
        qs = qs.filter(
            Q(origin_branch=user.branch) | Q(destination_branch=user.branch)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get('page'))
    branches = Branch.objects.filter(is_active=True)

    return render(request, 'inventory/transfer_list.html', {
        'page_obj': page, 'branches': branches,
        'status_choices': StockTransfer.STATUS_CHOICES,
        'status_filter': status_filter,
    })


@login_required
def transfer_create(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        origin_id = data.get('origin_branch')
        destination_id = data.get('destination_branch')
        items = data.get('items', [])
        notes = data.get('notes', '')

        if not items:
            return JsonResponse({'success': False, 'message': 'Debe agregar al menos un producto.'})

        try:
            origin = Branch.objects.get(pk=origin_id, is_active=True)
            destination = Branch.objects.get(pk=destination_id, is_active=True)
        except Branch.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Sucursal no válida.'})

        if origin == destination:
            return JsonResponse({'success': False, 'message': 'Las sucursales deben ser distintas.'})

        try:
            with transaction.atomic():
                transfer = StockTransfer.objects.create(
                    origin_branch=origin, destination_branch=destination,
                    notes=notes, created_by=request.user, status='en_transito'
                )
                for item_data in items:
                    product = Product.objects.select_for_update().get(pk=item_data['product_id'])
                    qty = int(item_data['quantity'])
                    stock = BranchStock.objects.select_for_update().get(
                        product=product, branch=origin
                    )
                    if stock.quantity < qty:
                        raise ValueError(f'Stock insuficiente de {product.name} en {origin.name}')
                    stock.quantity -= qty
                    stock.save()
                    StockTransferItem.objects.create(
                        transfer=transfer, product=product, quantity=qty
                    )
                    StockMovement.objects.create(
                        product=product, branch=origin,
                        movement_type='transferencia_salida', quantity=-qty,
                        reason=f'Transferencia {transfer.transfer_number}',
                        reference=transfer, created_by=request.user
                    )
        except ValueError as e:
            return JsonResponse({'success': False, 'message': str(e)})

        return JsonResponse({'success': True, 'transfer_number': transfer.transfer_number})
    return JsonResponse({'success': False})


@login_required
def transfer_detail(request, pk):
    transfer = get_object_or_404(
        StockTransfer.objects.select_related(
            'origin_branch', 'destination_branch', 'created_by'
        ).prefetch_related('items__product'), pk=pk
    )
    return render(request, 'inventory/transfer_detail.html', {'transfer': transfer})


@login_required
def transfer_complete(request, pk):
    transfer = get_object_or_404(StockTransfer, pk=pk)
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        received_items = data.get('items', [])

        if transfer.status != 'en_transito':
            return JsonResponse({'success': False, 'message': 'La transferencia no está en tránsito.'})

        if not request.user.can_access_branch(transfer.destination_branch):
            return JsonResponse({'success': False, 'message': 'Sin permisos para esta sucursal.'})

        try:
            with transaction.atomic():
                for item_data in received_items:
                    item = StockTransferItem.objects.get(
                        pk=item_data['item_id'], transfer=transfer
                    )
                    qty_received = int(item_data['quantity_received'])
                    item.quantity_received = qty_received
                    item.save()

                    stock, _ = BranchStock.objects.select_for_update().get_or_create(
                        product=item.product,
                        branch=transfer.destination_branch,
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
            return JsonResponse({'success': False, 'message': str(e)})

        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


@login_required
def low_stock_list(request):
    user = request.user
    qs = BranchStock.objects.filter(
        quantity__lte=F('product__min_stock')
    ).select_related('product__category', 'branch')

    if not user.is_superadmin:
        qs = qs.filter(branch=user.branch)

    data = [{
        'product': bs.product.name,
        'sku': bs.product.sku,
        'branch': bs.branch.name,
        'quantity': bs.quantity,
        'min_stock': bs.product.min_stock,
    } for bs in qs]
    return JsonResponse({'success': True, 'data': data})
