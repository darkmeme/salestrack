from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('products/', views.product_list, name='product_list'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('sales/', views.create_sale, name='create_sale'),
    path('dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),
    path('inventory/low-stock/', views.low_stock, name='low_stock'),
    path('branches/', views.branch_list, name='branch_list'),
    path('transfers/', views.transfer_create, name='transfer_create'),
    path('transfers/<int:pk>/complete/', views.transfer_complete, name='transfer_complete'),
]
