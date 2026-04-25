from .models import Branch, SystemSettings


def global_context(request):
    if not request.user.is_authenticated:
        return {}

    context = {}
    user = request.user

    if user.is_superadmin:
        context['all_branches'] = Branch.objects.filter(is_active=True)
        branch_id = request.session.get('active_branch_id')
        if branch_id:
            try:
                context['active_branch'] = Branch.objects.get(pk=branch_id, is_active=True)
            except Branch.DoesNotExist:
                context['active_branch'] = None
        else:
            context['active_branch'] = None
    else:
        context['active_branch'] = user.branch
        context['all_branches'] = []

    # System settings available in every template
    settings = SystemSettings.get()
    context['sys'] = settings

    return context
