from django.contrib import admin
from .models import Warehouse, Location, Product, AuditLog


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'rows_count', 'columns_count', 'created_at']
    search_fields = ['name', 'description']
    list_filter = ['created_at']
    fields = ['name', 'description', 'rows_count', 'columns_count']


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['warehouse', 'row', 'column', 'is_active', 'notes']
    list_filter = ['warehouse', 'is_active', 'row', 'column']
    search_fields = ['row', 'column', 'notes']
    ordering = ['warehouse', 'row', 'column']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['product_number', 'name', 'category', 'location', 'quantity', 'created_at']
    list_filter = ['category', 'created_at', 'location']
    search_fields = ['product_number', 'name', 'category', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['product_number']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'product_number', 'quantity_before', 'quantity_after', 'quantity_change', 'user', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['product_number', 'notes', 'user']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'

