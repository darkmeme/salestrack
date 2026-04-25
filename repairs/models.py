from django.db import models
from django.utils import timezone


class Repair(models.Model):
    STATUS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_reparacion', 'En Reparación'),
        ('reparado', 'Reparado'),
        ('entregado', 'Entregado'),
    ]

    STATUS_COLORS = {
        'pendiente': 'warning',
        'en_reparacion': 'primary',
        'reparado': 'success',
        'entregado': 'secondary',
    }

    repair_number = models.CharField(max_length=30, unique=True, editable=False, verbose_name='N° Orden')

    # Customer
    customer = models.ForeignKey(
        'sales.Customer', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='repairs'
    )
    customer_name = models.CharField(max_length=150, verbose_name='Nombre del cliente')
    customer_phone = models.CharField(max_length=20, blank=True, verbose_name='Teléfono')

    # Device
    brand = models.CharField(max_length=100, verbose_name='Marca')
    model = models.CharField(max_length=100, verbose_name='Modelo')
    imei = models.CharField(max_length=40, blank=True, verbose_name='IMEI / N° Serie')
    color = models.CharField(max_length=50, blank=True, verbose_name='Color')

    # Repair info
    diagnosis = models.TextField(verbose_name='Diagnóstico / Falla reportada')
    comments = models.TextField(blank=True, verbose_name='Comentarios internos')
    estimated_cost = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name='Costo estimado'
    )
    final_cost = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name='Costo final'
    )

    # Assignment
    branch = models.ForeignKey(
        'core.Branch', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='repairs', verbose_name='Sucursal'
    )
    technician = models.ForeignKey(
        'core.UserProfile', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_repairs', verbose_name='Técnico asignado'
    )
    received_by = models.ForeignKey(
        'core.UserProfile', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='received_repairs', verbose_name='Recibido por'
    )

    # Linked sale (created when charging the repair)
    sale = models.OneToOneField(
        'sales.Sale', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='repair', verbose_name='Venta'
    )

    # Status & dates
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendiente', verbose_name='Estado')
    received_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de ingreso')
    estimated_delivery = models.DateField(null=True, blank=True, verbose_name='Entrega estimada')
    repaired_at = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de reparación')
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de entrega')

    class Meta:
        verbose_name = 'Reparación'
        verbose_name_plural = 'Reparaciones'
        ordering = ['-received_at']

    def __str__(self):
        return f'{self.repair_number} — {self.brand} {self.model}'

    def save(self, *args, **kwargs):
        if not self.repair_number:
            from django.db import transaction
            today = timezone.now().strftime('%Y%m%d')
            prefix = f'REP-{today}-'
            with transaction.atomic():
                count = (
                    Repair.objects.select_for_update()
                    .filter(repair_number__startswith=prefix)
                    .count() + 1
                )
                self.repair_number = f'{prefix}{count:04d}'
        super().save(*args, **kwargs)

    @property
    def status_color(self):
        return self.STATUS_COLORS.get(self.status, 'secondary')

    @property
    def is_editable(self):
        return self.status not in ('entregado',)
