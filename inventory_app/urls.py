from django.urls import path
from . import views

app_name = 'inventory_app'

urlpatterns = [
    path('', views.home, name='home'),
    path('api/search/', views.search_products, name='search_products'),
    path('api/confirm-products/', views.confirm_products, name='confirm_products'),
    path('api/products/', views.get_products_list, name='products_list'),
    
    # إدارة المستودع
    path('manage/', views.manage_warehouse, name='manage_warehouse'),
    path('api/grid/', views.get_warehouse_grid, name='get_grid'),
    path('api/add-row/', views.add_row, name='add_row'),
    path('api/add-column/', views.add_column, name='add_column'),
    path('api/delete-row/', views.delete_row, name='delete_row'),
    path('api/delete-column/', views.delete_column, name='delete_column'),
    
    # لوحة التحكم
    path('dashboard/', views.warehouse_dashboard, name='dashboard'),
    
    # إدارة المنتجات الكاملة
    path('products/', views.products_list, name='products_list'),
    path('products/add/', views.product_add, name='product_add'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('products/<int:product_id>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:product_id>/delete/', views.product_delete, name='product_delete'),
    path('products/<int:product_id>/assign/', views.assign_location_to_product, name='assign_location'),
    
    # إدارة المستودعات
    path('warehouses/', views.warehouses_list, name='warehouses_list'),
    path('warehouses/<int:warehouse_id>/', views.warehouse_detail, name='warehouse_detail'),
    
    # إدارة الأماكن
    path('locations/', views.locations_list, name='locations_list'),
    
    # سجلات العمليات
    path('audit-logs/', views.audit_logs, name='audit_logs'),
]

