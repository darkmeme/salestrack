from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
import decimal


class Customer(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['name']

    def __str__(self):
        return self.name


class Sale(models.Model):
    STATUS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]

    invoice_number = models.CharField(max_length=40, unique=True, editable=False)
    branch = models.ForeignKey('core.Branch', on_delete=models.CASCADE, related_name='sales')
    customer = models.ForeignKey(
        Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales'
    )
    seller = models.ForeignKey(
        'core.UserProfile', on_delete=models.SET_NULL, null=True, related_name='sales'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completada')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['-created_at']

    def __str__(self):
        return self.invoice_number

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            import uuid
            today = timezone.now().strftime('%Y%m%d')
            branch_code = self.branch.code.replace('-', '') if self.branch_id else 'XXX'
            # Use select_for_update inside its own atomic block to serialize counting
            from django.db import transaction as _tx
            with _tx.atomic():
                count = (
                    Sale.objects.select_for_update()
                    .filter(invoice_number__startswith=f'VTA-{branch_code}-{today}-')
                    .count() + 1
                )
                self.invoice_number = f'VTA-{branch_code}-{today}-{count:04d}'
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)

    def recalculate_totals(self):
        from core.models import SystemSettings
        TAX_RATE = SystemSettings.get_tax_rate()
        items = self.items.all()
        subtotal = sum(item.subtotal for item in items)
        discount = self.discount
        taxable_amount = subtotal - discount
        tax = (taxable_amount * TAX_RATE).quantize(decimal.Decimal('0.01'))
        total = taxable_amount + tax
        Sale.objects.filter(pk=self.pk).update(
            subtotal=subtotal,
            tax=tax,
            total=total,
        )


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Ítem de Venta'
        verbose_name_plural = 'Ítems de Venta'

    def __str__(self):
        return f'{self.product.name} x{self.quantity}'

    def save(self, *args, **kwargs):
        self.subtotal = (self.unit_price * self.quantity) - self.discount
        super().save(*args, **kwargs)


class Payment(models.Model):
    METHOD_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia Bancaria'),
    ]

    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='payments')
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'

    def __str__(self):
        return f'{self.get_method_display()} - S/{self.amount}'


@receiver(post_save, sender=SaleItem)
@receiver(post_delete, sender=SaleItem)
def update_sale_totals(sender, instance, **kwargs):
    instance.sale.recalculate_totals()
