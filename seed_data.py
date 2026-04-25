#!/usr/bin/env python
"""
Script de seed para SalesTrack.
Ejecutar: python seed_data.py  (con el venv activo)
"""
import os
import sys
import django
import decimal
import random
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salestrack.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.db import transaction
from core.models import Branch, UserProfile
from inventory.models import Category, Supplier, Product, BranchStock, StockMovement
from sales.models import Customer, Sale, SaleItem, Payment


def run():
    print("=== SalesTrack Seed Data ===\n")

    # ── Branches ──────────────────────────────────────────────────────────────
    print("Creando sucursales...")
    with transaction.atomic():
        branch_central = Branch.objects.get_or_create(
            code='SUC-001',
            defaults={'name': 'Central', 'address': 'Av. Principal 123, Lima',
                      'phone': '01-234-5678', 'email': 'central@salestrack.pe'}
        )[0]
        branch_norte = Branch.objects.get_or_create(
            code='SUC-002',
            defaults={'name': 'Norte', 'address': 'Av. Universitaria 456, Los Olivos',
                      'phone': '01-234-5679', 'email': 'norte@salestrack.pe'}
        )[0]
        branch_sur = Branch.objects.get_or_create(
            code='SUC-003',
            defaults={'name': 'Sur', 'address': 'Av. Atocongo 789, SJM',
                      'phone': '01-234-5680', 'email': 'sur@salestrack.pe'}
        )[0]
    branches = [branch_central, branch_norte, branch_sur]
    print(f"  OK {len(branches)} sucursales")

    # ── Users ──────────────────────────────────────────────────────────────────
    print("Creando usuarios...")
    with transaction.atomic():
        superadmin = _create_user('admin', 'Admin', 'SalesTrack', 'admin123', 'superadmin', None)
        admin_c  = _create_user('admin_central', 'Carlos', 'Gonzalez', 'pass1234', 'branch_admin', branch_central)
        admin_n  = _create_user('admin_norte', 'Maria', 'Rodriguez', 'pass1234', 'branch_admin', branch_norte)
        admin_s  = _create_user('admin_sur', 'Pedro', 'Flores', 'pass1234', 'branch_admin', branch_sur)
        cashier_c = _create_user('cajero_central', 'Ana', 'Torres', 'pass1234', 'cashier', branch_central)
        cashier_n = _create_user('cajero_norte', 'Luis', 'Vargas', 'pass1234', 'cashier', branch_norte)
        cashier_s = _create_user('cajero_sur', 'Rosa', 'Huaman', 'pass1234', 'cashier', branch_sur)
        Branch.objects.filter(pk=branch_central.pk).update(manager=admin_c)
        Branch.objects.filter(pk=branch_norte.pk).update(manager=admin_n)
        Branch.objects.filter(pk=branch_sur.pk).update(manager=admin_s)
    print("  OK 7 usuarios creados")

    # ── Categories ─────────────────────────────────────────────────────────────
    print("Creando categorias...")
    with transaction.atomic():
        cats = {}
        for name in ['Electronica', 'Ropa', 'Alimentos', 'Hogar', 'Deportes']:
            cats[name] = Category.objects.get_or_create(name=name)[0]
    print(f"  OK {len(cats)} categorias")

    # ── Suppliers ──────────────────────────────────────────────────────────────
    with transaction.atomic():
        supplier1 = Supplier.objects.get_or_create(
            name='TechSupply SAC', defaults={'email': 'ventas@techsupply.pe', 'phone': '01-555-0001'}
        )[0]

    # ── Products ───────────────────────────────────────────────────────────────
    print("Creando 40 productos...")
    product_data = [
        ('Laptop HP 15',           'ELEC-001', 'Electronica', 2499.90, 1800.00),
        ('Mouse Inalambrico Logitech', 'ELEC-002', 'Electronica', 89.90, 45.00),
        ('Teclado Mecanico',       'ELEC-003', 'Electronica', 149.90, 75.00),
        ('Monitor 24 FHD',         'ELEC-004', 'Electronica', 599.90, 380.00),
        ('Auriculares Bluetooth',  'ELEC-005', 'Electronica', 179.90, 90.00),
        ('Webcam HD 1080p',        'ELEC-006', 'Electronica', 129.90, 65.00),
        ('USB Hub 7 puertos',      'ELEC-007', 'Electronica', 59.90,  25.00),
        ('SSD 500GB',              'ELEC-008', 'Electronica', 259.90, 150.00),
        ('Cargador USB-C 65W',     'ELEC-009', 'Electronica', 79.90,  35.00),
        ('Cable HDMI 2m',          'ELEC-010', 'Electronica', 29.90,  10.00),
        ('Polo Basico Algodon',    'ROPA-001', 'Ropa',        39.90,  15.00),
        ('Jeans Slim Fit',         'ROPA-002', 'Ropa',        89.90,  35.00),
        ('Zapatillas Deportivas',  'ROPA-003', 'Ropa',        149.90, 70.00),
        ('Casaca Impermeable',     'ROPA-004', 'Ropa',        199.90, 90.00),
        ('Polo Cuello V',          'ROPA-005', 'Ropa',        34.90,  14.00),
        ('Pantalon Cargo',         'ROPA-006', 'Ropa',        79.90,  32.00),
        ('Calcetines Pack x5',     'ROPA-007', 'Ropa',        24.90,   8.00),
        ('Buzo Deportivo',         'ROPA-008', 'Ropa',        119.90, 55.00),
        ('Arroz Extra 5kg',        'ALIM-001', 'Alimentos',   19.90,  12.00),
        ('Aceite Vegetal 1L',      'ALIM-002', 'Alimentos',    8.90,   5.00),
        ('Leche Evaporada Pack x6','ALIM-003', 'Alimentos',   22.90,  14.00),
        ('Azucar Rubia 1kg',       'ALIM-004', 'Alimentos',    4.90,   2.50),
        ('Harina Sin Preparar 1kg','ALIM-005', 'Alimentos',    5.90,   3.00),
        ('Sal de Mesa 1kg',        'ALIM-006', 'Alimentos',    2.90,   1.00),
        ('Cafe Grano 250g',        'ALIM-007', 'Alimentos',   18.90,  10.00),
        ('Licuadora 2L',           'HOGAR-001','Hogar',       129.90, 65.00),
        ('Olla Arrocera 1.8L',     'HOGAR-002','Hogar',        99.90, 48.00),
        ('Sarten Antiadherente',   'HOGAR-003','Hogar',        79.90, 38.00),
        ('Aspiradora Portatil',    'HOGAR-004','Hogar',       189.90, 95.00),
        ('Plancha Vapor',          'HOGAR-005','Hogar',        89.90, 42.00),
        ('Juego de Sabanas Queen', 'HOGAR-006','Hogar',        69.90, 32.00),
        ('Almohada Fibra x2',      'HOGAR-007','Hogar',        49.90, 22.00),
        ('Balon de Futbol N5',     'DEP-001',  'Deportes',    59.90,  25.00),
        ('Raqueta de Tenis',       'DEP-002',  'Deportes',   149.90,  70.00),
        ('Mancuernas 5kg x2',      'DEP-003',  'Deportes',    79.90,  38.00),
        ('Colchoneta Yoga 6mm',    'DEP-004',  'Deportes',    49.90,  20.00),
        ('Cuerda de Saltar',       'DEP-005',  'Deportes',    19.90,   8.00),
        ('Guantes de Boxeo',       'DEP-006',  'Deportes',    89.90,  40.00),
        ('Pelota de Basquet',      'DEP-007',  'Deportes',    69.90,  30.00),
        ('Botella Termica 750ml',  'DEP-008',  'Deportes',    39.90,  16.00),
    ]
    products = []
    with transaction.atomic():
        for name, sku, cat_name, price, cost in product_data:
            p = Product.objects.get_or_create(
                sku=sku,
                defaults={
                    'name': name, 'category': cats[cat_name], 'supplier': supplier1,
                    'price': decimal.Decimal(str(price)), 'cost': decimal.Decimal(str(cost)),
                    'min_stock': 5,
                }
            )[0]
            products.append(p)
    print(f"  OK {len(products)} productos")

    # ── Branch Stock ───────────────────────────────────────────────────────────
    print("Creando stock por sucursal...")
    with transaction.atomic():
        for product in products:
            for branch in branches:
                qty = random.randint(10, 50)
                stock, created = BranchStock.objects.get_or_create(
                    product=product, branch=branch, defaults={'quantity': qty}
                )
                if not created:
                    stock.quantity = qty
                    stock.save()
    print(f"  OK Stock para {len(products) * len(branches)} combinaciones")

    # ── Customers ──────────────────────────────────────────────────────────────
    print("Creando 15 clientes...")
    customer_data = [
        ('Juan Perez',     'juan.perez@gmail.com',       '987654321'),
        ('Maria Garcia',   'maria.garcia@gmail.com',     '987654322'),
        ('Carlos Lopez',   'carlos.lopez@outlook.com',   '987654323'),
        ('Ana Martinez',   'ana.martinez@yahoo.com',     '987654324'),
        ('Luis Rodriguez', 'luis.rodriguez@gmail.com',   '987654325'),
        ('Rosa Sanchez',   'rosa.sanchez@gmail.com',     '987654326'),
        ('Pedro Flores',   'pedro.flores@outlook.com',   '987654327'),
        ('Carmen Diaz',    'carmen.diaz@gmail.com',      '987654328'),
        ('Jorge Herrera',  'jorge.herrera@gmail.com',    '987654329'),
        ('Patricia Mora',  'patricia.mora@yahoo.com',    '987654330'),
        ('Roberto Castro', 'roberto.castro@gmail.com',   '987654331'),
        ('Elena Vargas',   'elena.vargas@gmail.com',     '987654332'),
        ('Miguel Torres',  'miguel.torres@outlook.com',  '987654333'),
        ('Lucia Reyes',    'lucia.reyes@gmail.com',      '987654334'),
        ('Fernando Quispe','fernando.quispe@gmail.com',  '987654335'),
    ]
    customers = []
    with transaction.atomic():
        for name, email, phone in customer_data:
            c = Customer.objects.get_or_create(
                email=email, defaults={'name': name, 'phone': phone}
            )[0]
            customers.append(c)
    print(f"  OK {len(customers)} clientes")

    # ── Sales (each in its own transaction for correct invoice numbering) ──────
    print("Creando 30 ventas...")
    branch_sellers = {
        branch_central: [admin_c, cashier_c],
        branch_norte:   [admin_n, cashier_n],
        branch_sur:     [admin_s, cashier_s],
    }
    sales_created = 0
    for i in range(30):
        branch   = random.choice(branches)
        seller   = random.choice(branch_sellers[branch])
        customer = random.choice(customers + [None] * 3)

        try:
            # Each sale is its own transaction so select_for_update sees committed rows
            with transaction.atomic():
                sale = Sale.objects.create(
                    branch=branch, customer=customer, seller=seller,
                    status='completada', discount=decimal.Decimal('0.00'),
                    notes='', subtotal=0, tax=0, total=0,
                )
                num_items = random.randint(1, 4)
                selected = random.sample(products, num_items)
                for product in selected:
                    qty = random.randint(1, 3)
                    stock_obj = BranchStock.objects.filter(
                        product=product, branch=branch, quantity__gte=qty
                    ).first()
                    if stock_obj:
                        SaleItem.objects.create(
                            sale=sale, product=product, quantity=qty,
                            unit_price=product.price,
                            discount=decimal.Decimal('0.00'),
                            subtotal=product.price * qty,
                        )
                        stock_obj.quantity -= qty
                        stock_obj.save()

                sale.refresh_from_db()
                if sale.total > 0:
                    Payment.objects.create(
                        sale=sale,
                        method=random.choice(['efectivo', 'tarjeta', 'transferencia']),
                        amount=sale.total,
                    )
                    sales_created += 1
        except Exception as e:
            print(f"  Venta {i+1} omitida: {e}")

    print(f"  OK {sales_created} ventas creadas")

    print("\n=== Seed completado exitosamente ===")
    print("\nCredenciales:")
    print("  superadmin     -> admin / admin123")
    print("  admin central  -> admin_central / pass1234")
    print("  admin norte    -> admin_norte / pass1234")
    print("  admin sur      -> admin_sur / pass1234")
    print("  cajero central -> cajero_central / pass1234")
    print("  cajero norte   -> cajero_norte / pass1234")
    print("  cajero sur     -> cajero_sur / pass1234")


def _create_user(username, first, last, password, role, branch):
    user, created = UserProfile.objects.get_or_create(
        username=username,
        defaults={
            'first_name': first, 'last_name': last,
            'role': role, 'branch': branch,
            'is_staff': role == 'superadmin',
            'is_superuser': role == 'superadmin',
        }
    )
    if created:
        user.set_password(password)
        user.save()
    return user


if __name__ == '__main__':
    run()
