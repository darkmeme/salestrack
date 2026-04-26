from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        ('repairs', '0002_repair_sale'),
    ]

    operations = [
        migrations.CreateModel(
            name='Technician',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, verbose_name='Nombre completo')),
                ('phone', models.CharField(blank=True, max_length=20, verbose_name='Teléfono')),
                ('email', models.EmailField(blank=True, verbose_name='Correo')),
                ('specialization', models.CharField(blank=True, max_length=150, verbose_name='Especialización')),
                ('notes', models.TextField(blank=True, verbose_name='Notas')),
                ('is_active', models.BooleanField(default=True, verbose_name='Activo')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('branch', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='technicians', to='core.branch', verbose_name='Sucursal')),
            ],
            options={
                'verbose_name': 'Técnico',
                'verbose_name_plural': 'Técnicos',
                'ordering': ['name'],
            },
        ),
        migrations.AlterField(
            model_name='repair',
            name='technician',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_repairs', to='repairs.technician', verbose_name='Técnico asignado'),
        ),
    ]
