"""
Decorators مخصصة للتحكم في الصلاحيات
جميع الصلاحيات مبنية في ملفات النظام الخاصة
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse


def admin_required(view_func):
    """تأكد من أن المستخدم مسؤول"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'يجب تسجيل الدخول أولاً')
            return redirect('login')
        
        # التحقق من UserProfile
        if hasattr(request.user, 'user_profile'):
            if not request.user.user_profile.is_admin():
                messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
                return redirect('inventory_app:home')
        elif not request.user.is_superuser:
            # إذا لم يكن لديه profile، نتحقق من superuser فقط
            messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
            return redirect('inventory_app:home')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def staff_required(view_func):
    """تأكد من أن المستخدم موظف أو مسؤول (أي مستخدم مسجل دخول)"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'يجب تسجيل الدخول أولاً')
            return redirect('login')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def exclude_maintenance(view_func):
    """منع الموظفين من الوصول لصفحات الصيانة - المسؤول فقط"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'يجب تسجيل الدخول أولاً')
            return redirect('login')
        
        # التحقق من الصلاحية
        can_access = False
        if hasattr(request.user, 'user_profile'):
            can_access = request.user.user_profile.can_access_maintenance()
        elif request.user.is_superuser:
            can_access = True
        
        if not can_access:
            messages.error(request, 'ليس لديك صلاحية للوصول لصفحات الصيانة')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'ليس لديك صلاحية للوصول'}, status=403)
            return redirect('inventory_app:home')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def exclude_admin_dashboard(view_func):
    """منع الموظفين من الوصول للوحة تحكم المسؤول - المسؤول فقط"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'يجب تسجيل الدخول أولاً')
            return redirect('login')
        
        # التحقق من الصلاحية
        can_access = False
        if hasattr(request.user, 'user_profile'):
            can_access = request.user.user_profile.can_access_admin_dashboard()
        elif request.user.is_superuser:
            can_access = True
        
        if not can_access:
            messages.error(request, 'ليس لديك صلاحية للوصول إلى لوحة تحكم المسؤول')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'ليس لديك صلاحية للوصول'}, status=403)
            return redirect('inventory_app:home')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def get_user_type(user):
    """الحصول على نوع المستخدم"""
    if not user.is_authenticated:
        return None
    
    if hasattr(user, 'user_profile'):
        return user.user_profile.user_type
    elif user.is_superuser:
        return 'admin'
    else:
        return 'staff'


def is_admin(user):
    """التحقق من كون المستخدم مسؤول"""
    if not user.is_authenticated:
        return False
    
    if hasattr(user, 'user_profile'):
        return user.user_profile.is_admin()
    return user.is_superuser


def is_staff(user):
    """التحقق من كون المستخدم موظف"""
    if not user.is_authenticated:
        return False
    
    if hasattr(user, 'user_profile'):
        return user.user_profile.is_staff_user()
    return False

