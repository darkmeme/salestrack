from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('new/', views.pos, name='pos'),
    path('new/search-products/', views.pos_search_products, name='pos_search_products'),
    path('new/create/', views.create_sale, name='create_sale'),

    path('', views.sale_list, name='sale_list'),
    path('<int:pk>/', views.sale_detail, name='sale_detail'),
    path('<int:pk>/cancel/', views.sale_cancel, name='sale_cancel'),
]
