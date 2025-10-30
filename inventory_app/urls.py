from django.urls import path
from . import views

app_name = 'inventory_app'

urlpatterns = [
    path('', views.home, name='home'),
    path('api/search/', views.search_products, name='search_products'),
    path('api/confirm-products/', views.confirm_products, name='confirm_products'),
    path('api/products/', views.get_products_list, name='products_list'),
    path('api/get-stats/', views.get_stats, name='get_stats'),
    
    # البحث السريع
    path('api/search-products/', views.quick_search_products, name='quick_search_products'),
    path('api/search-locations/', views.quick_search_locations, name='quick_search_locations'),
    
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
    path('products/<int:product_id>/move/', views.move_product_with_shift, name='move_product_with_shift'),
    path('api/delete-products-bulk/', views.delete_products_bulk, name='delete_products_bulk'),
    
    # تصدير البيانات
    path('export/products/excel/', views.export_products_excel, name='export_products_excel'),
    path('export/products/pdf/', views.export_products_pdf, name='export_products_pdf'),
    
    # إدارة المستودعات
    path('warehouses/', views.warehouses_list, name='warehouses_list'),
    path('warehouses/<int:warehouse_id>/', views.warehouse_detail, name='warehouse_detail'),
    
    # إدارة الأماكن
    path('locations/', views.locations_list, name='locations_list'),
    path('api/update-location-notes/', views.update_location_notes, name='update_location_notes'),
    
    # سجلات العمليات
    path('audit-logs/', views.audit_logs, name='audit_logs'),
    
    # التقارير اليومية
    path('daily-reports/', views.daily_reports, name='daily_reports'),
    path('api/save-daily-report/', views.save_daily_report, name='save_daily_report'),
    path('daily-reports-archive/', views.daily_reports_archive, name='daily_reports_archive'),
    path('daily-report/<int:report_id>/', views.daily_report_detail, name='daily_report_detail'),
    
    # النسخ الاحتياطي والاستعادة
    path('backup-restore/', views.backup_restore_page, name='backup_restore'),
    path('api/export-backup/', views.export_backup, name='export_backup'),
    path('api/import-backup/', views.import_backup, name='import_backup'),
    
    # حذف البيانات
    path('data-deletion/', views.data_deletion_page, name='data_deletion'),
    path('api/delete-data/', views.delete_data, name='delete_data'),
    
    # إدارة الطلبات المسحوبة
    path('orders/', views.orders_list, name='orders_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('api/delete-order/<int:order_id>/', views.delete_order, name='delete_order'),
]

