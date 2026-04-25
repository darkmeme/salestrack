from django.db import models
from django.contrib.auth.models import AbstractUser
import decimal


class Branch(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    manager = models.ForeignKey(
        'UserProfile', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='managed_branches'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Sucursal'
        verbose_name_plural = 'Sucursales'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.code})'


class UserProfile(AbstractUser):
    ROLE_CHOICES = [
        ('superadmin', 'Super Administrador'),
        ('branch_admin', 'Administrador de Sucursal'),
        ('cashier', 'Cajero'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='cashier')
    branch = models.ForeignKey(
        Branch, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='users'
    )
    phone = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'

    @property
    def is_superadmin(self):
        return self.role == 'superadmin'

    @property
    def is_branch_admin(self):
        return self.role == 'branch_admin'

    @property
    def is_cashier(self):
        return self.role == 'cashier'

    def can_access_branch(self, branch):
        if self.is_superadmin:
            return True
        return self.branch == branch


class SystemSettings(models.Model):
    # Moneda e impuesto
    currency_symbol = models.CharField(max_length=10, default='L')
    currency_name = models.CharField(max_length=50, default='Lempiras')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=15.00)
    tax_name = models.CharField(max_length=20, default='ISV')
    # Datos de la tienda
    store_name = models.CharField(max_length=100, default='SalesTrack')
    store_logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    store_address = models.TextField(blank=True, default='')
    store_phone = models.CharField(max_length=30, blank=True, default='')
    store_email = models.EmailField(blank=True, default='')
    # Factura
    invoice_header = models.TextField(blank=True, default='')
    invoice_footer = models.TextField(blank=True, default='Gracias por su compra.')
    invoice_show_logo = models.BooleanField(default=True)
    invoice_show_tax_detail = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Configuracion del Sistema'
        verbose_name_plural = 'Configuracion del Sistema'

    def __str__(self):
        return f'Configuracion ({self.currency_symbol} / {self.tax_name} {self.tax_rate}%)'

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={
            'currency_symbol': 'L',
            'currency_name': 'Lempiras',
            'tax_rate': decimal.Decimal('15.00'),
            'tax_name': 'ISV',
            'store_name': 'SalesTrack',
        })
        return obj

    @classmethod
    def get_tax_rate(cls):
        return cls.get().tax_rate / 100

    @classmethod
    def get_currency(cls):
        return cls.get().currency_symbol
