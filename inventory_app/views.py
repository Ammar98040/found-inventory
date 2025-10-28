from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db import models as db_models
from .models import Product, Location, Warehouse, AuditLog, DailyReportArchive
import json
from django.core import serializers
from datetime import datetime


def home(request):
    """الصفحة الرئيسية - البحث عن المنتجات"""
    return render(request, 'inventory_app/home.html')


@csrf_exempt
@transaction.atomic
def confirm_products(request):
    """تأكيد أخذ المنتجات وخصم الكميات"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            products_list = data.get('products', [])
            
            # Extract product numbers for efficient batch query
            product_numbers = [item.get('number', '').strip() for item in products_list if item.get('number', '').strip()]
            
            # Optimize: Batch query with select_for_update to lock rows
            products_dict = {
                p.product_number: p 
                for p in Product.objects.filter(product_number__in=product_numbers).select_for_update()
            }
            
            updated_products = []
            
            for item in products_list:
                product_number = item.get('number', '').strip()
                requested_quantity = int(item.get('quantity', 0))
                
                # Fast lookup
                product = products_dict.get(product_number)
                
                if not product:
                    return JsonResponse({
                        'success': False,
                        'error': f'المنتج {product_number} غير موجود'
                    })
                
                if product.quantity >= requested_quantity:
                    old_quantity = product.quantity
                    product.quantity -= requested_quantity
                    product.save()
                    
                    # تسجيل العملية في السجل
                    AuditLog.objects.create(
                        action='quantity_taken',
                        product=product,
                        product_number=product_number,
                        quantity_before=old_quantity,
                        quantity_after=product.quantity,
                        quantity_change=-requested_quantity,
                        notes=f'تم سحب {requested_quantity} من المنتج',
                        user=request.user.username if request.user.is_authenticated else 'Guest'
                    )
                    
                    updated_products.append({
                        'product_number': product_number,
                        'old_quantity': old_quantity,
                        'new_quantity': product.quantity,
                        'quantity_taken': requested_quantity
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': f'الكمية غير كافية للمنتج {product_number}'
                    })
            
            return JsonResponse({
                'success': True,
                'updated_products': updated_products,
                'message': f'تم خصم {len(updated_products)} منتج'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)


@csrf_exempt
def search_products(request):
    """البحث عن المنتجات من خلال أرقامهم"""
    if request.method == 'POST':
        data = json.loads(request.body)
        products_list = data.get('products', [])
        
        # Extract product numbers for efficient batch query
        product_numbers = [item.get('product_number', '').strip() for item in products_list if item.get('product_number', '').strip()]
        
        # Optimize: Use select_related to avoid N+1 queries and batch query
        products = Product.objects.filter(product_number__in=product_numbers).select_related('location')
        
        # Create a dictionary for fast lookup
        products_dict = {p.product_number: p for p in products}
        
        results = []
        
        for item in products_list:
            product_number = item.get('product_number', '').strip()
            requested_quantity = int(item.get('quantity', 0))
            
            if not product_number:
                continue
            
            # Fast lookup from dictionary
            product = products_dict.get(product_number)
            
            if product:
                locations_data = []
                if product.location:
                    grid_pos = product.location.get_grid_position()
                    locations_data.append({
                        'id': product.location.id,
                        'full_location': product.location.full_location,
                        'row': product.location.row,
                        'column': product.location.column,
                        'x': grid_pos['x'],
                        'y': grid_pos['y'],
                        'notes': product.location.notes,
                    })
                
                result = {
                    'product_number': product.product_number,
                    'name': product.name,
                    'category': product.category,
                    'quantity': product.quantity,
                    'locations': locations_data,
                    'found': True,
                }
                
                if requested_quantity > 0:
                    result['requested_quantity'] = requested_quantity
                
                results.append(result)
            else:
                results.append({
                    'product_number': product_number,
                    'requested_quantity': requested_quantity,
                    'found': False,
                    'error': 'المنتج غير موجود في قاعدة البيانات'
                })
        
        return JsonResponse({'results': results}, json_dumps_params={'ensure_ascii': False})
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)


@require_http_methods(["GET"])
def get_products_list(request):
    products = Product.objects.all()[:100]
    products_data = [{'number': p.product_number, 'name': p.name} for p in products]
    return JsonResponse({'products': products_data}, json_dumps_params={'ensure_ascii': False})


def manage_warehouse(request):
    """صفحة إدارة المستودع"""
    warehouse = Warehouse.objects.first()
    if not warehouse:
        warehouse = Warehouse.objects.create(name='المستودع الرئيسي', rows_count=6, columns_count=15)
    
    return render(request, 'inventory_app/manage_warehouse.html', {'warehouse': warehouse})


@require_http_methods(["GET"])
def get_warehouse_grid(request):
    """الحصول على شبكة المستودع"""
    warehouse = Warehouse.objects.first()
    if not warehouse:
        return JsonResponse({'error': 'لا يوجد مستودع'}, status=404)
    
    # Optimize query with prefetch_related
    locations = Location.objects.filter(warehouse=warehouse).prefetch_related('products')
    grid_data = {}
    
    for location in locations:
        key = f"{location.row},{location.column}"
        # Use prefetched products
        products = list(location.products.all())
        grid_data[key] = {
            'row': location.row,
            'column': location.column,
            'notes': location.notes,
            'is_active': location.is_active,
            'has_products': len(products) > 0,
            'products': [p.product_number for p in products],
        }
    
    return JsonResponse({
        'rows': warehouse.rows_count,
        'columns': warehouse.columns_count,
        'grid': grid_data
    })


@require_http_methods(["POST"])
@csrf_exempt
def add_row(request):
    """إضافة صف جديد"""
    warehouse = Warehouse.objects.first()
    if not warehouse:
        return JsonResponse({'error': 'لا يوجد مستودع'}, status=404)
    
    try:
        with transaction.atomic():
            warehouse.rows_count += 1
            warehouse.save()
            
            for col in range(1, warehouse.columns_count + 1):
                Location.objects.create(
                    warehouse=warehouse,
                    row=warehouse.rows_count,
                    column=col
                )
            
            return JsonResponse({'success': True, 'new_rows_count': warehouse.rows_count})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@csrf_exempt
def add_column(request):
    """إضافة عمود جديد"""
    warehouse = Warehouse.objects.first()
    if not warehouse:
        return JsonResponse({'error': 'لا يوجد مستودع'}, status=404)
    
    try:
        with transaction.atomic():
            warehouse.columns_count += 1
            warehouse.save()
            
            for row in range(1, warehouse.rows_count + 1):
                Location.objects.create(
                    warehouse=warehouse,
                    row=row,
                    column=warehouse.columns_count
                )
            
            return JsonResponse({'success': True, 'new_columns_count': warehouse.columns_count})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@csrf_exempt
def delete_row(request):
    """حذف صف"""
    warehouse = Warehouse.objects.first()
    if not warehouse:
        return JsonResponse({'error': 'لا يوجد مستودع'}, status=404)
    
    try:
        row_num = int(request.POST.get('row'))
        
        with transaction.atomic():
            Location.objects.filter(warehouse=warehouse, row=row_num).delete()
            warehouse.rows_count -= 1
            warehouse.save()
            
            return JsonResponse({'success': True, 'new_rows_count': warehouse.rows_count})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@csrf_exempt
def delete_column(request):
    """حذف عمود"""
    warehouse = Warehouse.objects.first()
    if not warehouse:
        return JsonResponse({'error': 'لا يوجد مستودع'}, status=404)
    
    try:
        col_num = int(request.POST.get('column'))
        
        with transaction.atomic():
            Location.objects.filter(warehouse=warehouse, column=col_num).delete()
            warehouse.columns_count -= 1
            warehouse.save()
            
            return JsonResponse({'success': True, 'new_columns_count': warehouse.columns_count})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def warehouse_dashboard(request):
    """لوحة تحكم المستودع"""
    # Use select_related for related data
    warehouse = Warehouse.objects.first()
    products_count = Product.objects.count()
    locations_count = Location.objects.count()
    total_capacity = warehouse.rows_count * warehouse.columns_count if warehouse else 0
    
    return render(request, 'inventory_app/dashboard.html', {
        'warehouse': warehouse,
        'products_count': products_count,
        'locations_count': locations_count,
        'total_capacity': total_capacity
    })


def products_list(request):
    """قائمة جميع المنتجات"""
    # Optimize query with select_related to avoid N+1 queries
    products = Product.objects.select_related('location').all().order_by('product_number')
    
    search = request.GET.get('search', '')
    if search:
        products = products.filter(
            product_number__icontains=search
        ) | products.filter(
            name__icontains=search
        )
    
    # Add pagination for performance
    from django.core.paginator import Paginator
    paginator = Paginator(products, 50)  # Show 50 products per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'inventory_app/products_list.html', {
        'products': page_obj,
        'page_obj': page_obj,
        'search': search
    })


def product_detail(request, product_id):
    """تفاصيل منتج"""
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'inventory_app/product_detail.html', {'product': product})


def product_add(request):
    """إضافة منتج جديد"""
    if request.method == 'POST':
        try:
            product = Product.objects.create(
                product_number=request.POST.get('product_number'),
                name=request.POST.get('name', ''),
                category=request.POST.get('category', ''),
                description=request.POST.get('description', ''),
                quantity=int(request.POST.get('quantity', 0) or 0)
            )
            
            # تسجيل العملية في السجل
            AuditLog.objects.create(
                action='added',
                product=product,
                product_number=product.product_number,
                quantity_before=0,
                quantity_after=product.quantity,
                quantity_change=product.quantity,
                notes=f'تم إضافة منتج جديد: {product.name}',
                user=request.user.username if request.user.is_authenticated else 'Guest'
            )
            
            messages.success(request, 'تم إضافة المنتج بنجاح')
            return redirect('inventory_app:product_detail', product_id=product.id)
        except Exception as e:
            messages.error(request, f'خطأ: {str(e)}')
    
    return render(request, 'inventory_app/product_add.html')


def product_edit(request, product_id):
    """تعديل منتج"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        try:
            # حفظ القيم القديمة
            old_product_number = product.product_number
            old_name = product.name
            old_category = product.category
            old_quantity = product.quantity
            
            # التعديل
            new_product_number = request.POST.get('product_number')
            new_name = request.POST.get('name', '')
            new_category = request.POST.get('category', '')
            new_quantity = int(request.POST.get('quantity', 0) or 0)
            
            product.product_number = new_product_number
            product.name = new_name
            product.category = new_category
            product.description = request.POST.get('description', '')
            product.quantity = new_quantity
            product.save()
            
            # تسجيل التغييرات في السجل
            changes = []
            if old_product_number != new_product_number:
                changes.append(f'رقم المنتج: {old_product_number} → {new_product_number}')
            if old_name != new_name:
                changes.append(f'الاسم: {old_name} → {new_name}')
            if old_category != new_category:
                changes.append(f'الفئة: {old_category} → {new_category}')
            if old_quantity != new_quantity:
                changes.append(f'الكمية: {old_quantity} → {new_quantity}')
            
            if changes:
                AuditLog.objects.create(
                    action='updated',
                    product=product,
                    product_number=product.product_number,
                    quantity_before=old_quantity,
                    quantity_after=new_quantity,
                    quantity_change=new_quantity - old_quantity,
                    notes='تغييرات: ' + ' | '.join(changes),
                    user=request.user.username if request.user.is_authenticated else 'Guest'
                )
            
            messages.success(request, 'تم تعديل المنتج بنجاح')
            return redirect('inventory_app:product_detail', product_id=product.id)
        except Exception as e:
            messages.error(request, f'خطأ: {str(e)}')
    
    return render(request, 'inventory_app/product_edit.html', {'product': product})


def product_delete(request, product_id):
    """حذف منتج"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product_number = product.product_number
        quantity = product.quantity
        name = product.name
        
        # تسجيل العملية قبل الحذف
        AuditLog.objects.create(
            action='deleted',
            product=product,
            product_number=product_number,
            quantity_before=quantity,
            quantity_after=0,
            quantity_change=-quantity,
            notes=f'تم حذف المنتج: {name}',
            user=request.user.username if request.user.is_authenticated else 'Guest'
        )
        
        product.delete()
        messages.success(request, f'تم حذف المنتج {product_number}')
        return redirect('inventory_app:products_list')
    
    return render(request, 'inventory_app/product_delete.html', {'product': product})


def assign_location_to_product(request, product_id):
    """ربط منتج بموقع واحد فقط"""
    # Optimize with select_related
    product = get_object_or_404(Product.objects.select_related('location'), id=product_id)
    warehouse = Warehouse.objects.first()
    
    if request.method == 'POST':
        location_id = request.POST.get('location')
        if location_id:
            new_location = Location.objects.get(id=location_id)
            old_location = product.location
            
            # التحقق من أن الموقع غير مشغول بمنتج آخر - use exists() for efficiency
            if new_location.products.exclude(id=product.id).exists():
                messages.error(request, 'هذا الموقع مشغول بمنتج آخر! اختر موقعاً آخر')
            else:
                product.location = new_location
                product.save()
                
                # تسجيل العملية
                old_location_str = old_location.full_location if old_location else 'بدون موقع'
                new_location_str = new_location.full_location
                
                AuditLog.objects.create(
                    action='location_assigned',
                    product=product,
                    product_number=product.product_number,
                    quantity_before=product.quantity,
                    quantity_after=product.quantity,
                    quantity_change=0,
                    notes=f'تغيير الموقع: {old_location_str} → {new_location_str}',
                    user=request.user.username if request.user.is_authenticated else 'Guest'
                )
                
                messages.success(request, f'تم ربط المنتج بالموقع {new_location_str} بنجاح')
        else:
            # إلغاء الربط
            if product.location:
                old_location_str = product.location.full_location
                product.location = None
                product.save()
                
                AuditLog.objects.create(
                    action='location_removed',
                    product=product,
                    product_number=product.product_number,
                    quantity_before=product.quantity,
                    quantity_after=product.quantity,
                    quantity_change=0,
                    notes=f'إلغاء ربط الموقع: {old_location_str}',
                    user=request.user.username if request.user.is_authenticated else 'Guest'
                )
                
                messages.success(request, 'تم إلغاء ربط الموقع')
        
        return redirect('inventory_app:product_detail', product_id=product.id)
    
    # Optimize query
    all_locations = Location.objects.filter(warehouse=warehouse).select_related('warehouse').order_by('row', 'column')
    
    # تحديد الأماكن الشاغرة والفارغة - optimize with values_list
    occupied_locations = set(
        Location.objects.filter(products__isnull=False)
        .values_list('id', flat=True)
    )
    
    return render(request, 'inventory_app/assign_location.html', {
        'product': product,
        'all_locations': all_locations,
        'current_location': product.location,
        'warehouse': warehouse,
        'occupied_locations': occupied_locations
    })


def warehouses_list(request):
    """قائمة المستودعات"""
    warehouses = Warehouse.objects.all()
    return render(request, 'inventory_app/warehouses_list.html', {'warehouses': warehouses})


def warehouse_detail(request, warehouse_id):
    """تفاصيل مستودع"""
    warehouse = get_object_or_404(Warehouse, id=warehouse_id)
    locations_count = Location.objects.filter(warehouse=warehouse).count()
    return render(request, 'inventory_app/warehouse_detail.html', {
        'warehouse': warehouse,
        'locations_count': locations_count
    })


def locations_list(request):
    """قائمة جميع الأماكن"""
    warehouse = Warehouse.objects.first()
    # Optimize with prefetch_related and select_related
    locations = Location.objects.filter(warehouse=warehouse).select_related('warehouse').prefetch_related('products').order_by('row', 'column')
    
    search = request.GET.get('search', '')
    if search:
        locations = locations.filter(notes__icontains=search)
    
    # Add pagination
    from django.core.paginator import Paginator
    paginator = Paginator(locations, 100)  # Show 100 locations per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'inventory_app/locations_list.html', {
        'locations': page_obj,
        'page_obj': page_obj,
        'warehouse': warehouse,
        'search': search
    })


@require_http_methods(["GET"])
def get_stats(request):
    """API للحصول على إحصائيات النظام"""
    try:
        from .models import Product, Location, Warehouse
        
        # إحصائيات المنتجات
        products_count = Product.objects.count()
        # المنتجات التي لها موقع (location ليست null)
        products_with_locations = Product.objects.filter(location__isnull=False).count()
        products_without_locations = products_count - products_with_locations
        
        # إحصائيات الأماكن
        locations_count = Location.objects.count()
        warehouse = Warehouse.objects.first()
        
        if warehouse:
            total_capacity = warehouse.rows_count * warehouse.columns_count
            # المواقع المشغولة (التي تحتوي على منتجات)
            # استخدام values_list للحصول على الـ IDs المميزة للأماكن المشغولة
            occupied_locations_ids = Product.objects.filter(location__isnull=False).values_list('location_id', flat=True).distinct()
            occupied_locations = len(occupied_locations_ids) if occupied_locations_ids else 0
            empty_locations = total_capacity - occupied_locations
        else:
            total_capacity = 0
            occupied_locations = 0
            empty_locations = 0
        
        return JsonResponse({
            # المنتجات
            'products_count': products_count,
            'products_with_locations': products_with_locations,
            'products_without_locations': products_without_locations,
            # الأماكن
            'locations_count': locations_count,
            'total_capacity': total_capacity,
            'occupied_locations': occupied_locations,
            'empty_locations': empty_locations,
            # معلومات المستودع
            'warehouse_rows': warehouse.rows_count if warehouse else 0,
            'warehouse_columns': warehouse.columns_count if warehouse else 0,
        }, json_dumps_params={'ensure_ascii': False})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def quick_search_products(request):
    """API للبحث السريع في المنتجات"""
    try:
        from .models import Product
        query = request.GET.get('q', '').strip()
        
        if not query:
            return JsonResponse([], safe=False, json_dumps_params={'ensure_ascii': False})
        
        # البحث في رقم المنتج واسمه
        products = Product.objects.filter(
            product_number__icontains=query
        ) | Product.objects.filter(
            name__icontains=query
        )
        
        products = products[:10]  # أول 10 نتائج
        
        results = []
        for product in products:
            results.append({
                'id': product.id,
                'product_number': product.product_number,
                'name': product.name,
                'location': product.location.full_location if product.location else None,
                'quantity': product.quantity
            })
        
        return JsonResponse(results, safe=False, json_dumps_params={'ensure_ascii': False})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def quick_search_locations(request):
    """API للبحث السريع في الأماكن"""
    try:
        from .models import Location
        query = request.GET.get('q', '').strip()
        
        if not query:
            return JsonResponse([], safe=False, json_dumps_params={'ensure_ascii': False})
        
        # البحث في المواقع (R1C1, R2C3, etc.)
        locations = Location.objects.filter(
            row__icontains=query
        ) | Location.objects.filter(
            column__icontains=query
        )
        
        locations = locations[:10]  # أول 10 نتائج
        
        results = []
        for location in locations:
            has_product = location.products.exists()
            results.append({
                'id': location.id,
                'full_location': location.full_location,
                'row': location.row,
                'column': location.column,
                'has_product': has_product,
                'warehouse': location.warehouse.name if location.warehouse else ''
            })
        
        return JsonResponse(results, safe=False, json_dumps_params={'ensure_ascii': False})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def audit_logs(request):
    """صفحة عرض سجلات العمليات"""
    from django.core.paginator import Paginator
    from django.db.models import Count

    # الاستعلام الأساسي + تحسينات
    base_qs = AuditLog.objects.select_related('product').all()

    search = request.GET.get('search', '')
    action_filter = request.GET.get('action', '')

    if search:
        base_qs = base_qs.filter(product_number__icontains=search)

    if action_filter:
        base_qs = base_qs.filter(action=action_filter)

    # إحصائيات كاملة قبل التقسيم لصفحات
    total_count = base_qs.count()
    counts_qs = base_qs.values('action').annotate(count=Count('id'))
    action_counts = {row['action']: row['count'] for row in counts_qs}

    # ترتيب لضمان تجميع منطقي داخل الصفحة (ثم الأحدث داخل كل نوع)
    ordered_qs = base_qs.order_by('action', '-created_at')

    # التقسيم لصفحات
    paginator = Paginator(ordered_qs, 100)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'inventory_app/audit_logs.html', {
        'logs': page_obj,
        'page_obj': page_obj,
        'search': search,
        'action_filter': action_filter,
        'total_count': total_count,
        'action_counts': action_counts,
    })


# ========== تصدير البيانات ==========

def export_products_excel(request):
    """تصدير قائمة المنتجات إلى Excel"""
    from django.http import HttpResponse
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter
    
    # إنشاء workbook جديد
    wb = Workbook()
    ws = wb.active
    ws.title = "المنتجات"
    
    # تنسيق النمط العربي
    arabic_font = Font(name='Arial', size=12, bold=True)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # رأس الجدول
    headers = ['#', 'رقم المنتج', 'الاسم', 'الفئة', 'الكمية', 'الموقع', 'تاريخ الإضافة']
    ws.append(headers)
    
    # تنسيق رأس الجدول
    header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col)
        cell.font = Font(name='Arial', size=12, bold=True, color='FFFFFF')
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='right', vertical='center', wrap_text=True)
        cell.border = border
    
    # جلب المنتجات
    products = Product.objects.all().order_by('product_number')
    
    # إضافة البيانات
    for idx, product in enumerate(products, start=1):
        location_text = product.location.full_location if product.location else 'لا يوجد موقع'
        
        row_data = [
            idx,
            product.product_number,
            product.name,
            product.category or '',
            product.quantity,
            location_text,
            product.created_at.strftime('%Y-%m-%d')
        ]
        
        ws.append(row_data)
        
        # تنسيق الصف
        for col in range(1, len(row_data) + 1):
            cell = ws.cell(row=idx + 1, column=col)
            cell.alignment = Alignment(horizontal='right', vertical='center', wrap_text=True)
            cell.border = border
            cell.font = Font(name='Arial', size=11)
    
    # ضبط عرض الأعمدة
    column_widths = [5, 15, 25, 15, 10, 12, 15]
    for col, width in enumerate(column_widths, start=1):
        ws.column_dimensions[get_column_letter(col)].width = width
    
    # إعداد الاستجابة
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="قائمة_المنتجات.xlsx"'
    
    wb.save(response)
    return response


def daily_reports(request):
    """صفحة التقارير اليومية السريعة"""
    from datetime import datetime, timedelta
    
    # تحديد نطاق التاريخ (اليوم)
    today = datetime.now().date()
    
    # فحص وحفظ تلقائي للتقارير السابقة غير المحفوظة
    _auto_save_daily_reports()
    
    # إحصائيات اليوم (استخدام created_at بدلاً من timestamp)
    today_logs = AuditLog.objects.filter(created_at__date=today)
    
    # إحصائيات المنتجات
    products_added = today_logs.filter(action='added').count()
    products_updated = today_logs.filter(action='updated').count()
    products_deleted = today_logs.filter(action='deleted').count()
    quantities_taken = today_logs.filter(action='quantity_taken').count()
    locations_assigned = today_logs.filter(action='location_assigned').count()
    
    # المنتجات الجديدة اليوم
    new_products = Product.objects.filter(created_at__date=today).order_by('-created_at')[:10]
    
    # آخر العمليات
    recent_logs = today_logs.order_by('-created_at')[:20]
    
    # إحصائيات الكميات
    quantity_changes = today_logs.filter(action__in=['added', 'quantity_taken']).aggregate(
        total_added=db_models.Sum('quantity_change', filter=db_models.Q(quantity_change__gt=0)),
        total_removed=db_models.Sum('quantity_change', filter=db_models.Q(quantity_change__lt=0))
    )
    
    context = {
        'today': today,
        'products_added': products_added,
        'products_updated': products_updated,
        'products_deleted': products_deleted,
        'quantities_taken': quantities_taken,
        'locations_assigned': locations_assigned,
        'new_products': new_products,
        'recent_logs': recent_logs,
        'total_added': quantity_changes['total_added'] or 0,
        'total_removed': abs(quantity_changes['total_removed'] or 0),
    }
    
    return render(request, 'inventory_app/daily_reports.html', context)


def _auto_save_daily_reports():
    """حفظ تلقائي للتقارير اليومية السابقة غير المحفوظة"""
    from datetime import datetime, timedelta
    
    try:
        # التحقق من آخر 7 أيام للحفظ التلقائي
        today = datetime.now().date()
        
        for day_offset in range(7):
            check_date = today - timedelta(days=day_offset)
            
            # تخطي اليوم الحالي
            if check_date == today:
                continue
            
            # التحقق من عدم وجود تقرير محفوظ لهذا التاريخ
            existing_report = DailyReportArchive.objects.filter(report_date=check_date).first()
            if existing_report:
                continue  # التقرير محفوظ مسبقاً
            
            # جلب بيانات هذا التاريخ
            date_logs = AuditLog.objects.filter(created_at__date=check_date)
            
            # إذا كانت هناك عمليات في هذا اليوم ولم يكن محفوظ، احفظه
            if date_logs.exists():
                products_added = date_logs.filter(action='added').count()
                products_updated = date_logs.filter(action='updated').count()
                products_deleted = date_logs.filter(action='deleted').count()
                quantities_taken = date_logs.filter(action='quantity_taken').count()
                locations_assigned = date_logs.filter(action='location_assigned').count()
                
                new_products = Product.objects.filter(created_at__date=check_date).order_by('-created_at')[:10]
                recent_logs = date_logs.order_by('-created_at')[:20]
                
                quantity_changes = date_logs.filter(action__in=['added', 'quantity_taken']).aggregate(
                    total_added=db_models.Sum('quantity_change', filter=db_models.Q(quantity_change__gt=0)),
                    total_removed=db_models.Sum('quantity_change', filter=db_models.Q(quantity_change__lt=0))
                )
                
                # إعداد البيانات للـ JSON
                report_data = {
                    'new_products': [
                        {
                            'product_number': p.product_number,
                            'name': p.name,
                            'category': p.category,
                            'quantity': p.quantity,
                            'location': p.location.full_location if p.location else None
                        } for p in new_products
                    ],
                    'recent_logs': [
                        {
                            'action': log.action,
                            'product_number': log.product_number,
                            'notes': log.notes,
                            'created_at': log.created_at.strftime('%Y-%m-%d %H:%M')
                        } for log in recent_logs
                    ]
                }
                
                # إنشاء التقرير المحفوظ
                hijri_date = convert_to_hijri(check_date)
                
                DailyReportArchive.objects.create(
                    report_date=check_date,
                    hijri_date=hijri_date,
                    products_added=products_added,
                    products_updated=products_updated,
                    products_deleted=products_deleted,
                    quantities_taken=quantities_taken,
                    locations_assigned=locations_assigned,
                    total_added=quantity_changes['total_added'] or 0,
                    total_removed=abs(quantity_changes['total_removed'] or 0),
                    report_data=report_data,
                    is_auto_saved=True  # علامة لحفظ تلقائي
                )
    except Exception as e:
        # في حالة حدوث خطأ، لا توقف العملية
        pass


def convert_to_hijri(gregorian_date):
    """تحويل التاريخ الميلادي إلى هجري"""
    try:
        from datetime import datetime
        # حساب التاريخ الهجري بطريقة تقريبية
        hijri_epoch = datetime(622, 7, 16)  # بداية التقويم الهجري
        days_diff = (gregorian_date - hijri_epoch.date()).days
        hijri_year = 1 + days_diff // 354  # السنة الهجرية حوالي 354 يوماً
        
        # شهر تقريبي
        remaining_days = days_diff % 354
        hijri_month = (remaining_days // 30) + 1
        hijri_day = remaining_days % 30
        
        hijri_months = ['محرم', 'صفر', 'ربيع الأول', 'ربيع الآخر', 'جمادى الأولى', 
                       'جمادى الآخرة', 'رجب', 'شعبان', 'رمضان', 'شوال', 'ذو القعدة', 'ذو الحجة']
        
        month_name = hijri_months[min(hijri_month - 1, 11)]
        
        return f"{hijri_day} {month_name} {hijri_year}"
    except:
        return f"تحويل التاريخ غير متاح"


def save_daily_report(request):
    """حفظ التقرير اليومي"""
    from datetime import datetime
    
    if request.method == 'POST':
        try:
            today = datetime.now().date()
            
            # التحقق من عدم وجود تقرير محفوظ لهذا اليوم
            existing_report = DailyReportArchive.objects.filter(report_date=today).first()
            if existing_report:
                return JsonResponse({
                    'success': False,
                    'message': 'تم حفظ تقرير اليوم مسبقاً'
                })
            
            # جلب بيانات اليوم
            today_logs = AuditLog.objects.filter(created_at__date=today)
            
            products_added = today_logs.filter(action='added').count()
            products_updated = today_logs.filter(action='updated').count()
            products_deleted = today_logs.filter(action='deleted').count()
            quantities_taken = today_logs.filter(action='quantity_taken').count()
            locations_assigned = today_logs.filter(action='location_assigned').count()
            
            new_products = Product.objects.filter(created_at__date=today).order_by('-created_at')[:10]
            recent_logs = today_logs.order_by('-created_at')[:20]
            
            quantity_changes = today_logs.filter(action__in=['added', 'quantity_taken']).aggregate(
                total_added=db_models.Sum('quantity_change', filter=db_models.Q(quantity_change__gt=0)),
                total_removed=db_models.Sum('quantity_change', filter=db_models.Q(quantity_change__lt=0))
            )
            
            # إعداد البيانات للـ JSON
            report_data = {
                'new_products': [
                    {
                        'product_number': p.product_number,
                        'name': p.name,
                        'category': p.category,
                        'quantity': p.quantity,
                        'location': p.location.full_location if p.location else None
                    } for p in new_products
                ],
                'recent_logs': [
                    {
                        'action': log.action,
                        'product_number': log.product_number,
                        'notes': log.notes,
                        'created_at': log.created_at.strftime('%Y-%m-%d %H:%M')
                    } for log in recent_logs
                ]
            }
            
            # إنشاء التقرير المحفوظ
            hijri_date = convert_to_hijri(today)
            
            DailyReportArchive.objects.create(
                report_date=today,
                hijri_date=hijri_date,
                products_added=products_added,
                products_updated=products_updated,
                products_deleted=products_deleted,
                quantities_taken=quantities_taken,
                locations_assigned=locations_assigned,
                total_added=quantity_changes['total_added'] or 0,
                total_removed=abs(quantity_changes['total_removed'] or 0),
                report_data=report_data
            )
            
            return JsonResponse({
                'success': True,
                'message': 'تم حفظ التقرير بنجاح'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطأ: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


def daily_reports_archive(request):
    """عرض السجل (أرشيف التقارير اليومية)"""
    search_query = request.GET.get('search', '')
    
    reports = DailyReportArchive.objects.all()
    
    if search_query:
        # البحث في التاريخ الميلادي والهجري
        reports = reports.filter(
            report_date__icontains=search_query
        ) | reports.filter(
            hijri_date__icontains=search_query
        )
    
    return render(request, 'inventory_app/daily_reports_archive.html', {
        'reports': reports,
        'search_query': search_query
    })


def daily_report_detail(request, report_id):
    """عرض تفاصيل تقرير محفوظ"""
    report = get_object_or_404(DailyReportArchive, id=report_id)
    
    return render(request, 'inventory_app/daily_report_detail.html', {
        'report': report
    })


def backup_restore_page(request):
    """صفحة النسخ الاحتياطي والاستعادة"""
    # إحصائيات البيانات
    stats = {
        'warehouses': Warehouse.objects.count(),
        'locations': Location.objects.count(),
        'products': Product.objects.count(),
        'audit_logs': AuditLog.objects.count(),
        'daily_reports': DailyReportArchive.objects.count(),
    }
    
    return render(request, 'inventory_app/backup_restore.html', {
        'stats': stats
    })


@csrf_exempt
@require_http_methods(["POST"])
def update_location_notes(request):
    """تحديث ملاحظات موقع"""
    try:
        data = json.loads(request.body)
        location_id = data.get('location_id')
        notes = data.get('notes', '')
        
        if not location_id:
            return JsonResponse({
                'success': False,
                'error': 'معرف الموقع مطلوب'
            })
        
        location = Location.objects.get(id=location_id)
        location.notes = notes
        location.save()
        
        return JsonResponse({
            'success': True,
            'message': 'تم حفظ الملاحظات بنجاح'
        })
        
    except Location.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'الموقع غير موجود'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@csrf_exempt
@require_http_methods(["POST"])
def export_backup(request):
    """تصدير النسخ الاحتياطي"""
    try:
        # جمع البيانات
        data = {
            'export_info': {
                'date': datetime.now().isoformat(),
                'version': '1.0',
                'description': 'نسخ احتياطي كامل من نظام إدارة المستودع'
            },
            'warehouses': json.loads(serializers.serialize('json', Warehouse.objects.all())),
            'locations': json.loads(serializers.serialize('json', Location.objects.all())),
            'products': json.loads(serializers.serialize('json', Product.objects.all())),
            'audit_logs': json.loads(serializers.serialize('json', AuditLog.objects.all())),
            'daily_reports': json.loads(serializers.serialize('json', DailyReportArchive.objects.all())),
        }
        
        # إنشاء ملف JSON
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        
        # إعداد الاستجابة
        filename = f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        response = HttpResponse(json_data, content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@csrf_exempt
@require_http_methods(["POST"])
def import_backup(request):
    """استيراد النسخ الاحتياطي"""
    try:
        if 'backup_file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'لم يتم إرسال ملف'
            })
        
        uploaded_file = request.FILES['backup_file']
        
        # قراءة الملف
        data = json.loads(uploaded_file.read().decode('utf-8'))
        
        # التحقق من صحة الملف
        if 'export_info' not in data:
            return JsonResponse({
                'success': False,
                'error': 'الملف غير صالح'
            })
        
        clear_existing = request.POST.get('clear_existing', 'false') == 'true'
        
        # بدء الاستيراد
        with transaction.atomic():
            if clear_existing:
                # حذف البيانات الموجودة
                AuditLog.objects.all().delete()
                Product.objects.all().delete()
                Location.objects.all().delete()
                Warehouse.objects.all().delete()
                DailyReportArchive.objects.all().delete()
            
            # استيراد البيانات
            if 'warehouses' in data:
                objects = serializers.deserialize('json', json.dumps(data['warehouses']))
                for obj in objects:
                    obj.save()
            
            if 'locations' in data:
                objects = serializers.deserialize('json', json.dumps(data['locations']))
                for obj in objects:
                    obj.save()
            
            if 'products' in data:
                objects = serializers.deserialize('json', json.dumps(data['products']))
                for obj in objects:
                    obj.save()
            
            if 'audit_logs' in data:
                objects = serializers.deserialize('json', json.dumps(data['audit_logs']))
                for obj in objects:
                    obj.save()
            
            if 'daily_reports' in data:
                objects = serializers.deserialize('json', json.dumps(data['daily_reports']))
                for obj in objects:
                    obj.save()
        
        return JsonResponse({
            'success': True,
            'message': 'تم الاستيراد بنجاح'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'الملف غير صالح'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def data_deletion_page(request):
    """صفحة حذف البيانات"""
    # إحصائيات البيانات
    stats = {
        'warehouses': Warehouse.objects.count(),
        'locations': Location.objects.count(),
        'products': Product.objects.count(),
        'audit_logs': AuditLog.objects.count(),
        'daily_reports': DailyReportArchive.objects.count(),
    }
    
    return render(request, 'inventory_app/data_deletion.html', {
        'stats': stats
    })


@csrf_exempt
@require_http_methods(["POST"])
@transaction.atomic
def delete_data(request):
    """حذف البيانات المحددة"""
    try:
        data = json.loads(request.body)
        
        # قراءة البيانات المحددة للحذف
        delete_products = data.get('delete_products', False)
        delete_locations = data.get('delete_locations', False)
        delete_warehouses = data.get('delete_warehouses', False)
        delete_audit_logs = data.get('delete_audit_logs', False)
        delete_daily_reports = data.get('delete_daily_reports', False)
        
        deleted_items = []
        
        # حذف البيانات المحددة
        if delete_products:
            count = Product.objects.count()
            Product.objects.all().delete()
            deleted_items.append(f'{count} منتج')
        
        if delete_warehouses:
            count = Warehouse.objects.count()
            Warehouse.objects.all().delete()
            deleted_items.append(f'{count} مستودع')
        
        if delete_locations:
            count = Location.objects.count()
            Location.objects.all().delete()
            deleted_items.append(f'{count} مكان')
        
        if delete_audit_logs:
            count = AuditLog.objects.count()
            AuditLog.objects.all().delete()
            deleted_items.append(f'{count} سجل عمليات')
        
        if delete_daily_reports:
            count = DailyReportArchive.objects.count()
            DailyReportArchive.objects.all().delete()
            deleted_items.append(f'{count} تقرير يومي')
        
        if not deleted_items:
            return JsonResponse({
                'success': False,
                'error': 'لم يتم تحديد أي بيانات للحذف'
            })
        
        return JsonResponse({
            'success': True,
            'message': f'تم حذف: {", ".join(deleted_items)}'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'البيانات غير صالحة'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

