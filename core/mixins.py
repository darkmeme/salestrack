from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


class BranchAccessMixin(LoginRequiredMixin):
    """
    Mixin que filtra el acceso por sucursal según el rol del usuario.
    - superadmin: acceso total
    - branch_admin: solo su sucursal, acceso a reportes
    - cashier: solo ventas en su sucursal, sin acceso a admin
    """
    admin_only = False
    superadmin_only = False

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if self.superadmin_only and not request.user.is_superadmin:
            raise PermissionDenied

        if self.admin_only and request.user.is_cashier:
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def get_branch_filter(self):
        user = self.request.user
        if user.is_superadmin:
            return None
        return user.branch

    def filter_by_branch(self, queryset, branch_field='branch'):
        branch = self.get_branch_filter()
        if branch is not None:
            return queryset.filter(**{branch_field: branch})
        return queryset

    def get_active_branch(self):
        user = self.request.user
        if user.is_superadmin:
            branch_id = self.request.session.get('active_branch_id')
            if branch_id:
                from core.models import Branch
                try:
                    return Branch.objects.get(pk=branch_id, is_active=True)
                except Branch.DoesNotExist:
                    pass
            return None
        return user.branch

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.models import Branch
        user = self.request.user
        context['active_branch'] = self.get_active_branch()
        if user.is_superadmin:
            context['all_branches'] = Branch.objects.filter(is_active=True)
        return context
