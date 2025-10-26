from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db import models as db_models
from .models import Product, Location, Warehouse, AuditLog
import json


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
            
            updated_products = []
            
            for item in products_list:
                product_number = item.get('number', '').strip()
                requested_quantity = int(item.get('quantity', 0))
                
                try:
                    product = Product.objects.get(product_number=product_number)
                    
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
                        
                except Product.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': f'المنتج {product_number} غير موجود'
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
        
        results = []
        
        for item in products_list:
            product_number = item.get('product_number', '').strip()
            requested_quantity = int(item.get('quantity', 0))
            
            if not product_number:
                continue
            
            try:
                product = Product.objects.get(product_number=product_number)
                
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
            except Product.DoesNotExist:
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
    
    locations = Location.objects.filter(warehouse=warehouse)
    grid_data = {}
    
    for location in locations:
        key = f"{location.row},{location.column}"
        products = location.products.all()
        grid_data[key] = {
            'row': location.row,
            'column': location.column,
            'notes': location.notes,
            'is_active': location.is_active,
            'has_products': products.exists(),
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
    products = Product.objects.all().order_by('product_number')
    
    search = request.GET.get('search', '')
    if search:
        products = products.filter(
            product_number__icontains=search
        ) | products.filter(
            name__icontains=search
        )
    
    return render(request, 'inventory_app/products_list.html', {
        'products': products,
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
    product = get_object_or_404(Product, id=product_id)
    warehouse = Warehouse.objects.first()
    
    if request.method == 'POST':
        location_id = request.POST.get('location')
        if location_id:
            new_location = Location.objects.get(id=location_id)
            old_location = product.location
            
            # التحقق من أن الموقع غير مشغول بمنتج آخر
            if new_location.products.filter(~db_models.Q(id=product.id)).exists():
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
    
    all_locations = Location.objects.filter(warehouse=warehouse).order_by('row', 'column')
    
    # تحديد الأماكن الشاغرة والفارغة
    occupied_locations = {loc.id for loc in Location.objects.filter(products__isnull=False)}
    
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
    locations = Location.objects.filter(warehouse=warehouse).order_by('row', 'column')
    
    search = request.GET.get('search', '')
    if search:
        locations = locations.filter(notes__icontains=search)
    
    return render(request, 'inventory_app/locations_list.html', {
        'locations': locations,
        'warehouse': warehouse,
        'search': search
    })


def audit_logs(request):
    """صفحة عرض سجلات العمليات"""
    logs = AuditLog.objects.all()
    
    search = request.GET.get('search', '')
    action_filter = request.GET.get('action', '')
    
    if search:
        logs = logs.filter(product_number__icontains=search)
    
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    # Limit to 100 after filtering
    logs = list(logs[:200])
    
    return render(request, 'inventory_app/audit_logs.html', {
        'logs': logs,
        'search': search,
        'action_filter': action_filter
    })

