from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:pk>/update/', views.product_update, name='product_update'),
    path('products/<int:pk>/adjust/', views.stock_adjust, name='stock_adjust'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('products/export/', views.product_export_csv, name='product_export'),

    path('transfers/', views.transfer_list, name='transfer_list'),
    path('transfers/create/', views.transfer_create, name='transfer_create'),
    path('transfers/<int:pk>/', views.transfer_detail, name='transfer_detail'),
    path('transfers/<int:pk>/complete/', views.transfer_complete, name='transfer_complete'),

    path('low-stock/', views.low_stock_list, name='low_stock'),
]
