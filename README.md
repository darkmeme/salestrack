# SalesTrack — Sistema de Ventas e Inventario Multi-Sucursal

Sistema web completo de ventas e inventario con soporte para múltiples sucursales, construido con Django 4.2 + Bootstrap 5.

## Requisitos

- Python 3.10+
- MySQL 8.x
- pip

## Instalación

### 1. Clonar y preparar el entorno

```bash
git clone <repo>
cd salestrack
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Crear la base de datos en MySQL

Conectarse a MySQL y ejecutar:

```sql
CREATE DATABASE salestrack CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
```

Editar `.env` con los valores reales:

```env
SECRET_KEY=clave-secreta-larga-y-aleatoria
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=salestrack
DB_USER=root
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=3306
```

### 5. Ejecutar migraciones

```bash
python manage.py makemigrations core inventory sales
python manage.py migrate
```

### 6. Cargar datos de prueba

```bash
python seed_data.py
```

### 7. Levantar el servidor

```bash
python manage.py runserver
```

Acceder a: [http://localhost:8000](http://localhost:8000)

---

## Credenciales de prueba

| Usuario         | Contraseña | Rol              | Sucursal   |
|-----------------|------------|------------------|------------|
| admin           | admin123   | Superadmin       | Todas      |
| admin_central   | pass1234   | Admin sucursal   | Central    |
| admin_norte     | pass1234   | Admin sucursal   | Norte      |
| admin_sur       | pass1234   | Admin sucursal   | Sur        |
| cajero_central  | pass1234   | Cajero           | Central    |
| cajero_norte    | pass1234   | Cajero           | Norte      |
| cajero_sur      | pass1234   | Cajero           | Sur        |

---

## Estructura del proyecto

```
salestrack/
├── core/           # Usuarios, sucursales, autenticación
├── inventory/      # Productos, stock, transferencias
├── sales/          # Ventas, POS, clientes
├── dashboard/      # Panel principal con KPIs y gráficos
├── reports/        # Reportes y exportaciones CSV
├── api/            # API REST con DRF
├── templates/      # Plantillas HTML
├── static/         # CSS y JavaScript
├── seed_data.py    # Datos de prueba
└── manage.py
```

## API REST

Base URL: `/api/v1/`

| Método | Endpoint                         | Descripción                          |
|--------|----------------------------------|--------------------------------------|
| GET    | `/products/?branch=`             | Productos con stock                  |
| GET    | `/products/{id}/`                | Detalle de producto                  |
| POST   | `/sales/`                        | Crear venta                          |
| GET    | `/dashboard/stats/?branch=`      | KPIs del dashboard                   |
| GET    | `/inventory/low-stock/?branch=`  | Productos con stock crítico          |
| GET    | `/branches/`                     | Sucursales activas                   |
| POST   | `/transfers/`                    | Crear transferencia                  |
| PATCH  | `/transfers/{id}/complete/`      | Confirmar recepción                  |

Todas las respuestas tienen el formato:
```json
{ "success": true, "data": {}, "message": "" }
```

## Roles y permisos

| Permiso                        | Superadmin | Admin | Cajero |
|-------------------------------|:----------:|:-----:|:------:|
| Ver todas las sucursales       | ✓          | ✗     | ✗      |
| Gestionar productos            | ✓          | ✓     | ✗      |
| Ajustar stock                  | ✓          | ✓     | ✗      |
| Crear transferencias           | ✓          | ✓     | ✗      |
| Realizar ventas                | ✓          | ✓     | ✓      |
| Anular ventas                  | ✓          | ✓     | ✗      |
| Ver reportes                   | ✓          | ✓     | ✗      |
| Comparativo multi-sucursal     | ✓          | ✗     | ✗      |
| Gestionar usuarios             | ✓          | ✗     | ✗      |
