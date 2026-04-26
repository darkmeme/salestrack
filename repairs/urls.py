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
    # Technicians
    path('technicians/', views.technician_list, name='technician_list'),
    path('technicians/create/', views.technician_create, name='technician_create'),
    path('technicians/<int:pk>/update/', views.technician_update, name='technician_update'),
    path('technicians/<int:pk>/toggle/', views.technician_toggle, name='technician_toggle'),
]
