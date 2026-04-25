from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from django.utils import timezone
import decimal
import json

from core.models import Branch
from inventory.models import Product, BranchStock, StockMovement
from .models import Customer, Sale, SaleItem, Payment
from .forms import CustomerForm, SaleFilterForm


@login_required
def pos(request):
    user = request.user
    branches = Branch.objects.filter(is_active=True) if user.is_superadmin else []
    active_branch = None
    if not user.is_superadmin:
        active_branch = user.branch
    else:
        branch_id = request.session.get('active_branch_id')
        if branch_id:
            try:
                active_branch = Branch.objects.get(pk=branch_id)
            except Branch.DoesNotExist:
                pass
    return render(request, 'sales/pos.html', {
        'branches': branches,
        'active_branch': active_branch,
    })


@login_required
def pos_search_products(request):
    branch_id = request.GET.get('branch')
    q = request.GET.get('q', '')
    user = request.user

    if not user.is_superadmin:
        branch_id = user.branch.pk if user.branch else None

    if not branch_id:
        return JsonResponse({'success': False, 'data': []})

    try:
        branch = Branch.objects.get(pk=branch_id)
    except Branch.DoesNotExist:
        return JsonResponse({'success': False, 'data': []})

    qs = BranchStock.objects.filter(
        branch=branch, quantity__gt=0, product__is_active=True
    ).select_related('product__category')

    if q:
        qs = qs.filter(
            Q(product__name__icontains=q) | Q(product__sku__icontains=q)
        )

    data = [{
        'id': bs.product.pk,
        'name': bs.product.name,
        'sku': bs.product.sku,
        'price': float(bs.product.price),
        'stock': bs.quantity,
    } for bs in qs[:20]]

    return JsonResponse({'success': True, 'data': data})


@login_required
def create_sale(request):
    if request.method != 'POST':
        return JsonResponse({'success': False})

    data = json.loads(request.body)
    branch_id = data.get('branch_id')
    customer_id = data.get('customer_id')
    items = data.get('items', [])
    discount_global = decimal.Decimal(str(data.get('discount', 0)))
    notes = data.get('notes', '')
    payment_method = data.get('payment_method', 'efectivo')
    payment_amount = decimal.Decimal(str(data.get('payment_amount', 0)))

    user = request.user
    if not user.is_superadmin:
        branch_id = user.branch.pk if user.branch else None

    if not branch_id or not items:
        return JsonResponse({'success': False, 'message': 'Datos incompletos.'})

    try:
        branch = Branch.objects.get(pk=branch_id, is_active=True)
    except Branch.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Sucursal no válida.'})

    from core.models import SystemSettings
    TAX_RATE = SystemSettings.get_tax_rate()

    try:
        with transaction.atomic():
            sale = Sale.objects.create(
                branch=branch,
                customer_id=customer_id or None,
                seller=request.user,
                discount=discount_global,
                notes=notes,
                status='completada',
                subtotal=0, tax=0, total=0,
            )

            for item_data in items:
                product = Product.objects.select_for_update().get(
                    pk=item_data['product_id'], is_active=True
                )
                qty = int(item_data['quantity'])
                unit_price = decimal.Decimal(str(item_data['unit_price']))
                item_discount = decimal.Decimal(str(item_data.get('discount', 0)))

                stock = BranchStock.objects.select_for_update().get(
                    product=product, branch=branch
                )
                if stock.quantity < qty:
                    raise ValueError(f'Stock insuficiente de "{product.name}"')

                SaleItem.objects.create(
                    sale=sale, product=product, quantity=qty,
                    unit_price=unit_price, discount=item_discount,
                    subtotal=(unit_price * qty) - item_discount,
                )

                stock.quantity -= qty
                stock.save()

                StockMovement.objects.create(
                    product=product, branch=branch,
                    movement_type='salida', quantity=-qty,
                    reason=f'Venta {sale.invoice_number}',
                    created_by=request.user
                )

            sale.refresh_from_db()

            Payment.objects.create(
                sale=sale, method=payment_method,
                amount=payment_amount,
            )

    except (ValueError, Product.DoesNotExist, BranchStock.DoesNotExist) as e:
        return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({
        'success': True,
        'invoice_number': sale.invoice_number,
        'sale_id': sale.pk,
    })


@login_required
def sale_list(request):
    user = request.user
    qs = Sale.objects.select_related('branch', 'customer', 'seller').order_by('-created_at')

    if not user.is_superadmin:
        qs = qs.filter(branch=user.branch)

    form = SaleFilterForm(request.GET)
    if form.is_valid():
        if user.is_superadmin and form.cleaned_data.get('branch'):
            qs = qs.filter(branch=form.cleaned_data['branch'])
        if form.cleaned_data.get('date_from'):
            qs = qs.filter(created_at__date__gte=form.cleaned_data['date_from'])
        if form.cleaned_data.get('date_to'):
            qs = qs.filter(created_at__date__lte=form.cleaned_data['date_to'])
        if form.cleaned_data.get('status'):
            qs = qs.filter(status=form.cleaned_data['status'])

    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'sales/sale_list.html', {
        'page_obj': page, 'form': form,
    })


@login_required
def sale_detail(request, pk):
    sale = get_object_or_404(
        Sale.objects.select_related('branch', 'customer', 'seller')
                    .prefetch_related('items__product', 'payments'),
        pk=pk
    )
    if not request.user.is_superadmin and sale.branch != request.user.branch:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    return render(request, 'sales/sale_detail.html', {'sale': sale})


@login_required
def sale_cancel(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.user.is_cashier:
        return JsonResponse({'success': False, 'message': 'Sin permisos.'}, status=403)
    if sale.status != 'completada':
        return JsonResponse({'success': False, 'message': 'Solo se pueden anular ventas completadas.'})

    if request.method == 'POST':
        try:
            with transaction.atomic():
                for item in sale.items.select_related('product').all():
                    stock, _ = BranchStock.objects.select_for_update().get_or_create(
                        product=item.product, branch=sale.branch, defaults={'quantity': 0}
                    )
                    stock.quantity += item.quantity
                    stock.save()
                    StockMovement.objects.create(
                        product=item.product, branch=sale.branch,
                        movement_type='ajuste', quantity=item.quantity,
                        reason=f'Anulación de venta {sale.invoice_number}',
                        created_by=request.user
                    )
                sale.status = 'cancelada'
                sale.save()
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})
