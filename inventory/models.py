from django.db import models
from django.db.models import Sum
from django.utils import timezone
import datetime


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['name']

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products'
    )
    supplier = models.ForeignKey(
        Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='products'
    )
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    min_stock = models.PositiveIntegerField(default=5)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.sku})'

    def get_stock_for_branch(self, branch):
        try:
            return self.branch_stocks.get(branch=branch).quantity
        except BranchStock.DoesNotExist:
            return 0

    def total_stock(self):
        return self.branch_stocks.aggregate(total=Sum('quantity'))['total'] or 0


class BranchStock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='branch_stocks')
    branch = models.ForeignKey('core.Branch', on_delete=models.CASCADE, related_name='stocks')
    quantity = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Stock por Sucursal'
        verbose_name_plural = 'Stocks por Sucursal'
        unique_together = ('product', 'branch')

    def __str__(self):
        return f'{self.product.name} @ {self.branch.name}: {self.quantity}'

    @property
    def is_low_stock(self):
        return self.quantity <= self.product.min_stock


class StockTransfer(models.Model):
    STATUS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_transito', 'En Tránsito'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]

    transfer_number = models.CharField(max_length=30, unique=True, editable=False)
    origin_branch = models.ForeignKey(
        'core.Branch', on_delete=models.CASCADE, related_name='transfers_out'
    )
    destination_branch = models.ForeignKey(
        'core.Branch', on_delete=models.CASCADE, related_name='transfers_in'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendiente')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        'core.UserProfile', on_delete=models.SET_NULL, null=True, related_name='transfers_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Transferencia de Stock'
        verbose_name_plural = 'Transferencias de Stock'
        ordering = ['-created_at']

    def __str__(self):
        return self.transfer_number

    def save(self, *args, **kwargs):
        if not self.transfer_number:
            today = timezone.now().strftime('%Y%m%d')
            count = StockTransfer.objects.filter(
                created_at__date=timezone.now().date()
            ).count() + 1
            self.transfer_number = f'TRF-{today}-{count:04d}'
        super().save(*args, **kwargs)


class StockTransferItem(models.Model):
    transfer = models.ForeignKey(StockTransfer, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    quantity_received = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Ítem de Transferencia'
        verbose_name_plural = 'Ítems de Transferencia'

    def __str__(self):
        return f'{self.product.name} x{self.quantity}'


class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('ajuste', 'Ajuste'),
        ('transferencia_salida', 'Transferencia Salida'),
        ('transferencia_entrada', 'Transferencia Entrada'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movements')
    branch = models.ForeignKey('core.Branch', on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=30, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()
    reason = models.TextField(blank=True)
    reference = models.ForeignKey(
        StockTransfer, on_delete=models.SET_NULL, null=True, blank=True, related_name='movements'
    )
    created_by = models.ForeignKey(
        'core.UserProfile', on_delete=models.SET_NULL, null=True, related_name='stock_movements'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Movimiento de Stock'
        verbose_name_plural = 'Movimientos de Stock'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_movement_type_display()} - {self.product.name} ({self.quantity})'
