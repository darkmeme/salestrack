from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.index, name='index'),
    path('sales/', views.sales_report, name='sales_report'),
    path('sales/csv/', views.sales_report_csv, name='sales_report_csv'),
    path('top-products/', views.top_products, name='top_products'),
    path('inventory/', views.inventory_valuation, name='inventory_valuation'),
    path('inventory/csv/', views.inventory_valuation_csv, name='inventory_valuation_csv'),
    path('branch-comparison/', views.branch_comparison, name='branch_comparison'),
]
