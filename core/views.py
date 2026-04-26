from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from .models import Branch, UserProfile, SystemSettings
from .forms import LoginForm, BranchForm, UserProfileForm, SystemSettingsForm
from .decorators import superadmin_required, branch_admin_required
from sales.models import Customer
from sales.forms import CustomerForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        return redirect(request.GET.get('next', 'dashboard:index'))
    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('core:login')


@login_required
@require_POST
def set_active_branch(request):
    branch_id = request.POST.get('branch_id')
    if branch_id == 'all':
        request.session.pop('active_branch_id', None)
    else:
        try:
            Branch.objects.get(pk=branch_id, is_active=True)
            request.session['active_branch_id'] = int(branch_id)
        except Branch.DoesNotExist:
            pass
    return JsonResponse({'success': True})


@superadmin_required
def branch_list(request):
    branches = Branch.objects.select_related('manager').all()
    form = BranchForm()
    return render(request, 'core/branch_list.html', {'branches': branches, 'form': form})


@superadmin_required
def branch_create(request):
    if request.method == 'POST':
        form = BranchForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sucursal creada correctamente.')
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False})


@superadmin_required
def branch_update(request, pk):
    branch = get_object_or_404(Branch, pk=pk)
    if request.method == 'POST':
        form = BranchForm(request.POST, instance=branch)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sucursal actualizada.')
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors})
    data = {
        'id': branch.pk, 'name': branch.name, 'code': branch.code,
        'address': branch.address, 'phone': branch.phone,
        'email': branch.email, 'is_active': branch.is_active,
    }
    return JsonResponse({'success': True, 'data': data})


@superadmin_required
def branch_delete(request, pk):
    branch = get_object_or_404(Branch, pk=pk)
    if request.method == 'POST':
        branch.is_active = False
        branch.save()
        messages.success(request, 'Sucursal desactivada.')
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


@superadmin_required
def user_list(request):
    users = UserProfile.objects.select_related('branch').all()
    paginator = Paginator(users, 25)
    page = paginator.get_page(request.GET.get('page'))
    all_branches = Branch.objects.filter(is_active=True)
    return render(request, 'core/user_list.html', {'page_obj': page, 'all_branches': all_branches})


@superadmin_required
def user_create(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario creado correctamente.')
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False})


@superadmin_required
def user_update(request, pk):
    user = get_object_or_404(UserProfile, pk=pk)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors})
    data = {
        'id': user.pk, 'username': user.username,
        'first_name': user.first_name, 'last_name': user.last_name,
        'email': user.email, 'role': user.role,
        'branch': user.branch_id, 'phone': user.phone,
        'is_active': user.is_active,
    }
    return JsonResponse({'success': True, 'data': data})


@superadmin_required
def user_delete(request, pk):
    if request.method == 'POST':
        user = get_object_or_404(UserProfile, pk=pk)
        if user == request.user:
            return JsonResponse({'success': False, 'message': 'No puedes eliminarte a ti mismo.'})
        user.is_active = False
        user.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


@login_required
def customer_list(request):
    qs = Customer.objects.all()
    q = request.GET.get('q', '')
    if q:
        qs = qs.filter(name__icontains=q) | qs.filter(email__icontains=q)
    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get('page'))
    form = CustomerForm()
    return render(request, 'core/customer_list.html', {
        'page_obj': page, 'form': form, 'q': q
    })


@login_required
def customer_create(request):
    if request.method == 'POST':
        import json as _json
        try:
            data = _json.loads(request.body)
        except Exception:
            data = request.POST
        form = CustomerForm(data)
        if form.is_valid():
            customer = form.save()
            return JsonResponse({'success': True, 'id': customer.pk, 'name': customer.name})
        return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False})


@login_required
def customer_update(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors})
    data = {
        'id': customer.pk, 'name': customer.name,
        'email': customer.email, 'phone': customer.phone,
        'address': customer.address,
    }
    return JsonResponse({'success': True, 'data': data})


@branch_admin_required
def customer_delete(request, pk):
    if request.method == 'POST':
        customer = get_object_or_404(Customer, pk=pk)
        if customer.sales.exists():
            return JsonResponse({'success': False, 'message': 'No se puede eliminar: el cliente tiene ventas asociadas.'})
        customer.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


@login_required
def customer_search(request):
    """JSON endpoint used by POS to search customers."""
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'success': True, 'data': []})
    qs = Customer.objects.filter(name__icontains=q) | Customer.objects.filter(phone__icontains=q)
    data = [{'id': c.pk, 'name': c.name, 'phone': c.phone, 'email': c.email} for c in qs[:10]]
    return JsonResponse({'success': True, 'data': data})


@superadmin_required
def system_settings(request):
    settings = SystemSettings.get()
    if request.method == 'POST':
        form = SystemSettingsForm(request.POST, request.FILES, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configuración guardada correctamente.')
            return redirect('core:system_settings')
    else:
        form = SystemSettingsForm(instance=settings)
    return render(request, 'core/settings.html', {'form': form, 'settings': settings})
