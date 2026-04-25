from django.urls import path
from . import views

app_name = 'repairs'

urlpatterns = [
    path('', views.repair_dashboard, name='dashboard'),
    path('list/', views.repair_list, name='repair_list'),
    path('create/', views.repair_create, name='repair_create'),
    path('<int:pk>/', views.repair_detail, name='repair_detail'),
    path('<int:pk>/update/', views.repair_update, name='repair_update'),
    path('<int:pk>/status/', views.repair_update_status, name='repair_update_status'),
    path('<int:pk>/charge/', views.repair_charge, name='repair_charge'),
]
