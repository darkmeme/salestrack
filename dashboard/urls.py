from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/stats/', views.stats_api, name='stats_api'),
    path('api/chart/sales-7days/', views.chart_sales_7days, name='chart_sales_7days'),
    path('api/chart/monthly-revenue/', views.chart_monthly_revenue, name='chart_monthly_revenue'),
    path('api/recent-sales/', views.recent_sales, name='recent_sales'),
    path('api/branch-summary/', views.branch_summary, name='branch_summary'),
]
