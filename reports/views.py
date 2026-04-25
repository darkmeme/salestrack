from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
import csv
import datetime

from core.decorators import branch_admin_required
from core.models import Branch
from inventory.models import BranchStock, Product, StockTransfer
from sales.models import Sale, SaleItem


@branch_admin_required
def index(request):
    branches = Branch.objects.filter(is_active=True) if request.user.is_superadmin else None
    return render(request, 'reports/index.html', {'branches': branches})


@branch_admin_required
def sales_report(request):
    user = request.user
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    branch_id = request.GET.get('branch')

    qs = Sale.objects.filter(status='completada').select_related('branch', 'customer', 'seller')

    if not user.is_superadmin:
        qs = qs.filter(branch=user.branch)
    elif branch_id:
        qs = qs.filter(branch_id=branch_id)

    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    totals = qs.aggregate(
        total_sales=Count('id'),
        total_revenue=Sum('total'),
        total_tax=Sum('tax'),
        total_discount=Sum('discount'),
    )

    data = {
        'sales': [{
            'invoice_number': s.invoice_number,
            'branch': s.branch.name,
            'customer': s.customer.name if s.customer else 'Sin cliente',
            'seller': s.seller.get_full_name() or s.seller.username if s.seller else '-',
            'subtotal': float(s.subtotal),
            'discount': float(s.discount),
            'tax': float(s.tax),
            'total': float(s.total),
            'date': s.created_at.strftime('%d/%m/%Y'),
        } for s in qs[:500]],
        'totals': {
            'count': totals['total_sales'] or 0,
            'revenue': float(totals['total_revenue'] or 0),
            'tax': float(totals['total_tax'] or 0),
            'discount': float(totals['total_discount'] or 0),
        }
    }
    return JsonResponse({'success': True, 'data': data})


@branch_admin_required
def sales_report_csv(request):
    user = request.user
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    branch_id = request.GET.get('branch')

    qs = Sale.objects.filter(status='completada').select_related('branch', 'customer', 'seller')
    if not user.is_superadmin:
        qs = qs.filter(branch=user.branch)
    elif branch_id:
        qs = qs.filter(branch_id=branch_id)
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="ventas.csv"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow(['N° Factura', 'Sucursal', 'Cliente', 'Vendedor', 'Subtotal', 'Descuento', 'IGV', 'Total', 'Fecha'])
    for s in qs:
        writer.writerow([
            s.invoice_number, s.branch.name,
            s.customer.name if s.customer else 'Sin cliente',
            s.seller.get_full_name() or s.seller.username if s.seller else '-',
            s.subtotal, s.discount, s.tax, s.total,
            s.created_at.strftime('%d/%m/%Y %H:%M'),
        ])
    return response


@branch_admin_required
def top_products(request):
    user = request.user
    branch_id = request.GET.get('branch')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    qs = SaleItem.objects.filter(sale__status='completada').select_related('product', 'sale__branch')

    if not user.is_superadmin:
        qs = qs.filter(sale__branch=user.branch)
    elif branch_id:
        qs = qs.filter(sale__branch_id=branch_id)

    if date_from:
        qs = qs.filter(sale__created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(sale__created_at__date__lte=date_to)

    top = (qs.values('product__name', 'product__sku')
             .annotate(total_qty=Sum('quantity'), total_revenue=Sum('subtotal'))
             .order_by('-total_qty')[:10])

    data = [{
        'name': item['product__name'],
        'sku': item['product__sku'],
        'total_qty': item['total_qty'],
        'total_revenue': float(item['total_revenue'] or 0),
    } for item in top]

    return JsonResponse({'success': True, 'data': data})


@branch_admin_required
def inventory_valuation(request):
    user = request.user
    branch_id = request.GET.get('branch')

    qs = BranchStock.objects.select_related('product__category', 'branch')

    if not user.is_superadmin:
        qs = qs.filter(branch=user.branch)
    elif branch_id:
        qs = qs.filter(branch_id=branch_id)

    data = [{
        'branch': bs.branch.name,
        'sku': bs.product.sku,
        'product': bs.product.name,
        'category': bs.product.category.name if bs.product.category else '',
        'quantity': bs.quantity,
        'cost': float(bs.product.cost),
        'price': float(bs.product.price),
        'cost_value': float(bs.product.cost * bs.quantity),
        'sale_value': float(bs.product.price * bs.quantity),
    } for bs in qs]

    return JsonResponse({'success': True, 'data': data})


@branch_admin_required
def inventory_valuation_csv(request):
    user = request.user
    branch_id = request.GET.get('branch')

    qs = BranchStock.objects.select_related('product__category', 'branch')
    if not user.is_superadmin:
        qs = qs.filter(branch=user.branch)
    elif branch_id:
        qs = qs.filter(branch_id=branch_id)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="inventario.csv"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow(['Sucursal', 'SKU', 'Producto', 'Categoría', 'Cantidad', 'Costo', 'Precio', 'Valor Costo', 'Valor Venta'])
    for bs in qs:
        writer.writerow([
            bs.branch.name, bs.product.sku, bs.product.name,
            bs.product.category.name if bs.product.category else '',
            bs.quantity, bs.product.cost, bs.product.price,
            bs.product.cost * bs.quantity, bs.product.price * bs.quantity,
        ])
    return response


@branch_admin_required
def branch_comparison(request):
    if not request.user.is_superadmin:
        return JsonResponse({'success': False, 'message': 'Solo superadmin.'}, status=403)

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    branches = Branch.objects.filter(is_active=True)
    result = []
    for branch in branches:
        qs = Sale.objects.filter(branch=branch, status='completada')
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        totals = qs.aggregate(count=Count('id'), revenue=Sum('total'))
        result.append({
            'branch': branch.name,
            'code': branch.code,
            'sales_count': totals['count'] or 0,
            'revenue': float(totals['revenue'] or 0),
        })

    return JsonResponse({'success': True, 'data': result})
