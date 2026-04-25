from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
import datetime

from core.models import Branch
from inventory.models import BranchStock, Product
from sales.models import Sale, Customer


@login_required
def index(request):
    return render(request, 'dashboard/index.html')


@login_required
def stats_api(request):
    user = request.user
    today = timezone.now().date()
    month_start = today.replace(day=1)

    branch_id = request.GET.get('branch')
    active_branch = None

    if user.is_superadmin and branch_id and branch_id != 'all':
        try:
            active_branch = Branch.objects.get(pk=branch_id, is_active=True)
        except Branch.DoesNotExist:
            pass
    elif not user.is_superadmin:
        active_branch = user.branch

    sale_filter = Q(status='completada')
    stock_filter = Q()
    if active_branch:
        sale_filter &= Q(branch=active_branch)
        stock_filter = Q(branch=active_branch)

    sales_today = Sale.objects.filter(sale_filter, created_at__date=today)
    sales_today_count = sales_today.count()
    sales_today_revenue = sales_today.aggregate(total=Sum('total'))['total'] or 0

    sales_month = Sale.objects.filter(sale_filter, created_at__date__gte=month_start)
    monthly_revenue = sales_month.aggregate(total=Sum('total'))['total'] or 0

    low_stock_count = BranchStock.objects.filter(
        stock_filter,
        quantity__lte=F('product__min_stock')
    ).count()

    customers_new = Customer.objects.filter(created_at__date__gte=month_start).count()

    data = {
        'sales_today': sales_today_count,
        'revenue_today': float(sales_today_revenue),
        'monthly_revenue': float(monthly_revenue),
        'low_stock_count': low_stock_count,
        'customers_new': customers_new,
    }
    return JsonResponse({'success': True, 'data': data})


@login_required
def chart_sales_7days(request):
    user = request.user
    branch_id = request.GET.get('branch')
    active_branch = None

    if user.is_superadmin and branch_id and branch_id != 'all':
        try:
            active_branch = Branch.objects.get(pk=branch_id, is_active=True)
        except Branch.DoesNotExist:
            pass
    elif not user.is_superadmin:
        active_branch = user.branch

    today = timezone.now().date()
    labels = []
    datasets = []

    if user.is_superadmin and not active_branch:
        branches = Branch.objects.filter(is_active=True)
        colors = ['#1a2942', '#2196F3', '#4CAF50', '#FF9800', '#E91E63', '#9C27B0']
        for i, branch in enumerate(branches):
            branch_data = []
            for day_offset in range(6, -1, -1):
                day = today - datetime.timedelta(days=day_offset)
                if i == 0:
                    labels.append(day.strftime('%d/%m'))
                revenue = Sale.objects.filter(
                    branch=branch, status='completada',
                    created_at__date=day
                ).aggregate(total=Sum('total'))['total'] or 0
                branch_data.append(float(revenue))
            datasets.append({
                'label': branch.name,
                'data': branch_data,
                'backgroundColor': colors[i % len(colors)] + '99',
                'borderColor': colors[i % len(colors)],
                'borderWidth': 2,
            })
    else:
        sale_filter = Q(status='completada')
        if active_branch:
            sale_filter &= Q(branch=active_branch)
        data_points = []
        for day_offset in range(6, -1, -1):
            day = today - datetime.timedelta(days=day_offset)
            labels.append(day.strftime('%d/%m'))
            revenue = Sale.objects.filter(
                sale_filter, created_at__date=day
            ).aggregate(total=Sum('total'))['total'] or 0
            data_points.append(float(revenue))
        datasets.append({
            'label': active_branch.name if active_branch else 'Todas las sucursales',
            'data': data_points,
            'borderColor': '#1a2942',
            'backgroundColor': 'rgba(26,41,66,0.1)',
            'fill': True,
            'tension': 0.4,
        })

    return JsonResponse({'success': True, 'data': {'labels': labels, 'datasets': datasets}})


@login_required
def chart_monthly_revenue(request):
    user = request.user
    today = timezone.now().date()
    labels = []
    datasets = []

    months = []
    for i in range(5, -1, -1):
        month = (today.replace(day=1) - datetime.timedelta(days=i * 30)).replace(day=1)
        months.append(month)
        labels.append(month.strftime('%b %Y'))

    if user.is_superadmin:
        branches = Branch.objects.filter(is_active=True)
        colors = ['#1a2942', '#2196F3', '#4CAF50', '#FF9800', '#E91E63', '#9C27B0']
        for i, branch in enumerate(branches):
            branch_data = []
            for month in months:
                if month.month == 12:
                    next_month = month.replace(year=month.year + 1, month=1)
                else:
                    next_month = month.replace(month=month.month + 1)
                revenue = Sale.objects.filter(
                    branch=branch, status='completada',
                    created_at__date__gte=month,
                    created_at__date__lt=next_month,
                ).aggregate(total=Sum('total'))['total'] or 0
                branch_data.append(float(revenue))
            datasets.append({
                'label': branch.name,
                'data': branch_data,
                'borderColor': colors[i % len(colors)],
                'tension': 0.4,
                'fill': False,
            })
    else:
        branch = user.branch
        data_points = []
        for month in months:
            if month.month == 12:
                next_month = month.replace(year=month.year + 1, month=1)
            else:
                next_month = month.replace(month=month.month + 1)
            revenue = Sale.objects.filter(
                branch=branch, status='completada',
                created_at__date__gte=month,
                created_at__date__lt=next_month,
            ).aggregate(total=Sum('total'))['total'] or 0
            data_points.append(float(revenue))
        datasets.append({
            'label': branch.name if branch else 'Mi sucursal',
            'data': data_points,
            'borderColor': '#1a2942',
            'tension': 0.4,
            'fill': False,
        })

    return JsonResponse({'success': True, 'data': {'labels': labels, 'datasets': datasets}})


@login_required
def recent_sales(request):
    user = request.user
    qs = Sale.objects.select_related('branch', 'customer', 'seller').order_by('-created_at')
    if not user.is_superadmin:
        qs = qs.filter(branch=user.branch)
    sales = qs[:10]
    data = [{
        'invoice_number': s.invoice_number,
        'branch': s.branch.name,
        'customer': s.customer.name if s.customer else 'Sin cliente',
        'seller': s.seller.get_full_name() or s.seller.username if s.seller else '-',
        'total': float(s.total),
        'status': s.get_status_display(),
        'created_at': s.created_at.strftime('%d/%m/%Y %H:%M'),
    } for s in sales]
    return JsonResponse({'success': True, 'data': data})


@login_required
def branch_summary(request):
    branches = Branch.objects.filter(is_active=True).prefetch_related('stocks', 'sales')
    today = timezone.now().date()
    summaries = []
    for branch in branches:
        sales_today = Sale.objects.filter(
            branch=branch, status='completada', created_at__date=today
        ).aggregate(count=Count('id'), total=Sum('total'))
        low_stock = BranchStock.objects.filter(
            branch=branch, quantity__lte=F('product__min_stock')
        ).count()
        summaries.append({
            'name': branch.name,
            'code': branch.code,
            'sales_today': sales_today['count'] or 0,
            'revenue_today': float(sales_today['total'] or 0),
            'low_stock': low_stock,
        })
    return JsonResponse({'success': True, 'data': summaries})
