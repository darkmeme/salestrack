from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.utils import timezone

from core.models import UserProfile
from .models import Repair
from .forms import RepairForm, RepairStatusForm, RepairFilterForm


def _branch_filter(user):
    if user.is_superadmin:
        return Q()
    return Q(branch=user.branch)


@login_required
def repair_dashboard(request):
    user = request.user
    base_q = _branch_filter(user)

    f = RepairFilterForm(request.GET)
    qs = Repair.objects.filter(base_q).select_related('technician', 'branch')

    if f.is_valid():
        if f.cleaned_data.get('date_from'):
            qs = qs.filter(received_at__date__gte=f.cleaned_data['date_from'])
        if f.cleaned_data.get('date_to'):
            qs = qs.filter(received_at__date__lte=f.cleaned_data['date_to'])
        if f.cleaned_data.get('technician'):
            qs = qs.filter(technician=f.cleaned_data['technician'])

    stats = {
        'pendiente':     qs.filter(status='pendiente').count(),
        'en_reparacion': qs.filter(status='en_reparacion').count(),
        'reparado':      qs.filter(status='reparado').count(),
        'entregado':     qs.filter(status='entregado').count(),
        'total':         qs.count(),
    }
    recent = qs.order_by('-received_at')[:15]

    tech_qs = UserProfile.objects.filter(is_active=True).exclude(role='superadmin')
    if not user.is_superadmin and user.branch:
        tech_qs = tech_qs.filter(branch=user.branch)

    return render(request, 'repairs/dashboard.html', {
        'stats': stats,
        'recent': recent,
        'filter_form': f,
        'technicians': tech_qs,
    })


@login_required
def repair_list(request):
    user = request.user
    base_q = _branch_filter(user)
    f = RepairFilterForm(request.GET)
    qs = Repair.objects.filter(base_q).select_related('technician', 'branch', 'received_by')

    if f.is_valid():
        if f.cleaned_data.get('q'):
            qs = qs.filter(repair_number__icontains=f.cleaned_data['q'])
        if f.cleaned_data.get('customer_name'):
            qs = qs.filter(customer_name__icontains=f.cleaned_data['customer_name'])
        if f.cleaned_data.get('imei'):
            qs = qs.filter(imei__icontains=f.cleaned_data['imei'])
        if f.cleaned_data.get('model'):
            qs = qs.filter(model__icontains=f.cleaned_data['model'])
        if f.cleaned_data.get('status'):
            qs = qs.filter(status=f.cleaned_data['status'])
        if f.cleaned_data.get('date_from'):
            qs = qs.filter(received_at__date__gte=f.cleaned_data['date_from'])
        if f.cleaned_data.get('date_to'):
            qs = qs.filter(received_at__date__lte=f.cleaned_data['date_to'])
        if f.cleaned_data.get('technician'):
            qs = qs.filter(technician=f.cleaned_data['technician'])

    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'repairs/repair_list.html', {
        'page_obj': page,
        'filter_form': f,
    })


@login_required
def repair_create(request):
    user = request.user
    branch = None if user.is_superadmin else user.branch

    if request.method == 'POST':
        form = RepairForm(request.POST, branch=branch)
        if form.is_valid():
            repair = form.save(commit=False)
            repair.received_by = user
            if not user.is_superadmin:
                repair.branch = user.branch
            else:
                from core.models import Branch
                branch_id = request.POST.get('branch_id')
                if branch_id:
                    try:
                        repair.branch = Branch.objects.get(pk=branch_id, is_active=True)
                    except Branch.DoesNotExist:
                        pass
            # Link to existing customer if selected
            customer_id = request.POST.get('customer_id')
            if customer_id:
                from sales.models import Customer
                try:
                    repair.customer = Customer.objects.get(pk=customer_id)
                except Customer.DoesNotExist:
                    pass
            repair.save()
            messages.success(request, f'Reparación {repair.repair_number} creada correctamente.')
            return redirect('repairs:repair_detail', pk=repair.pk)
    else:
        form = RepairForm(branch=branch)

    from core.models import Branch
    branches = Branch.objects.filter(is_active=True) if user.is_superadmin else []
    return render(request, 'repairs/repair_form.html', {
        'form': form,
        'branches': branches,
        'title': 'Nueva Reparación',
    })


@login_required
def repair_detail(request, pk):
    user = request.user
    repair = get_object_or_404(
        Repair.objects.select_related('branch', 'technician', 'received_by', 'customer'),
        pk=pk
    )
    if not user.is_superadmin and repair.branch != user.branch:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    return render(request, 'repairs/repair_detail.html', {'repair': repair})


@login_required
def repair_update(request, pk):
    user = request.user
    repair = get_object_or_404(Repair, pk=pk)
    if not user.is_superadmin and repair.branch != user.branch:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    branch = None if user.is_superadmin else user.branch
    if request.method == 'POST':
        form = RepairForm(request.POST, instance=repair, branch=branch)
        if form.is_valid():
            updated = form.save(commit=False)
            customer_id = request.POST.get('customer_id')
            if customer_id:
                from sales.models import Customer
                try:
                    updated.customer = Customer.objects.get(pk=customer_id)
                except Customer.DoesNotExist:
                    pass
            elif not customer_id:
                updated.customer = None
            updated.save()
            messages.success(request, 'Reparación actualizada.')
            return redirect('repairs:repair_detail', pk=repair.pk)
    else:
        form = RepairForm(instance=repair, branch=branch)

    from core.models import Branch
    branches = Branch.objects.filter(is_active=True) if user.is_superadmin else []
    return render(request, 'repairs/repair_form.html', {
        'form': form,
        'repair': repair,
        'branches': branches,
        'title': f'Editar — {repair.repair_number}',
    })


@login_required
def repair_update_status(request, pk):
    repair = get_object_or_404(Repair, pk=pk)
    user = request.user
    if not user.is_superadmin and repair.branch != user.branch:
        return JsonResponse({'success': False, 'message': 'Sin permisos.'}, status=403)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        comments = request.POST.get('comments', '')
        final_cost = request.POST.get('final_cost', '')

        if new_status not in dict(Repair.STATUS_CHOICES):
            return JsonResponse({'success': False, 'message': 'Estado no válido.'})

        repair.status = new_status
        if comments:
            if repair.comments:
                repair.comments += f'\n[{timezone.now().strftime("%d/%m/%Y %H:%M")}] {comments}'
            else:
                repair.comments = comments
        if final_cost:
            try:
                repair.final_cost = float(final_cost)
            except ValueError:
                pass
        if new_status == 'reparado' and not repair.repaired_at:
            repair.repaired_at = timezone.now()
        if new_status == 'entregado' and not repair.delivered_at:
            repair.delivered_at = timezone.now()
        repair.save()
        messages.success(request, f'Estado actualizado a "{repair.get_status_display()}".')
        return JsonResponse({'success': True, 'status': new_status, 'label': repair.get_status_display()})

    return JsonResponse({'success': False})


@login_required
def repair_charge(request, pk):
    repair = get_object_or_404(Repair, pk=pk)
    user = request.user

    if not user.is_superadmin and repair.branch != user.branch:
        return JsonResponse({'success': False, 'message': 'Sin permisos.'}, status=403)

    if repair.sale_id:
        return JsonResponse({'success': False, 'message': 'Esta reparación ya fue cobrada.'})

    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido.'}, status=405)

    try:
        payment_method = request.POST.get('payment_method', 'efectivo')
        amount_paid = Decimal(request.POST.get('amount_paid', '0'))
        reference = request.POST.get('reference', '')

        from core.models import SystemSettings
        from sales.models import Sale, Payment

        cfg = SystemSettings.get()
        tax_rate = cfg.tax_rate / Decimal('100')

        subtotal = repair.final_cost
        tax = (subtotal * tax_rate).quantize(Decimal('0.01'))
        total = subtotal + tax

        branch = repair.branch or user.branch
        sale = Sale(
            branch=branch,
            customer=repair.customer,
            seller=user,
            status='completada',
            subtotal=subtotal,
            discount=Decimal('0'),
            tax=tax,
            total=total,
            notes=f'Cobro reparación {repair.repair_number} — {repair.brand} {repair.model} ({repair.customer_name})',
        )
        sale.save()
        # Set totals directly (no SaleItems, signal won't fire)
        Sale.objects.filter(pk=sale.pk).update(subtotal=subtotal, tax=tax, total=total)

        Payment.objects.create(
            sale=sale,
            method=payment_method,
            amount=amount_paid,
            reference=reference,
        )

        repair.sale = sale
        repair.status = 'entregado'
        if not repair.delivered_at:
            repair.delivered_at = timezone.now()
        repair.save()

        return JsonResponse({
            'success': True,
            'invoice_number': sale.invoice_number,
            'total': str(total),
            'cambio': str(max(Decimal('0'), amount_paid - total)),
        })

    except (InvalidOperation, Exception) as e:
        return JsonResponse({'success': False, 'message': str(e)})
