from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Branch, UserProfile


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'phone', 'email', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']


@admin.register(UserProfile)
class UserProfileAdmin(UserAdmin):
    list_display = ['username', 'get_full_name', 'role', 'branch', 'is_active']
    list_filter = ['role', 'branch', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Perfil SalesTrack', {'fields': ('role', 'branch', 'phone')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Perfil SalesTrack', {'fields': ('role', 'branch', 'phone')}),
    )
