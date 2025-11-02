from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from django.utils import timezone


class Warehouse(models.Model):
    """نموذج المستودع - يحتوي على معلومات المستودع"""
    name = models.CharField(max_length=200, verbose_name='اسم المستودع')
    description = models.TextField(blank=True, null=True, verbose_name='الوصف')
    
    # أبعاد الشبكة
    rows_count = models.IntegerField(default=6, validators=[MinValueValidator(1)], verbose_name='عدد الصفوف')
    columns_count = models.IntegerField(default=15, validators=[MinValueValidator(1)], verbose_name='عدد الأعمدة')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    
    class Meta:
        verbose_name = 'مستودع'
        verbose_name_plural = 'المستودعات'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_grid_dimensions(self):
        """إرجاع أبعاد الشبكة"""
        return {
            'rows': self.rows_count,
            'columns': self.columns_count
        }


class Location(models.Model):
    """نموذج الموقع داخل المستودع - يمثل خلية في الشبكة"""
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='locations', verbose_name='المستودع')
    
    # إحداثيات الشبكة (الصف والعمود)
    row = models.IntegerField(validators=[MinValueValidator(1)], verbose_name='الخط (Row)')
    column = models.IntegerField(validators=[MinValueValidator(1)], verbose_name='العمود (Column)')
    
    # معلومات إضافية
    notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    
    class Meta:
        verbose_name = 'موقع'
        verbose_name_plural = 'الأماكن'
        ordering = ['warehouse', 'row', 'column']
        unique_together = ['warehouse', 'row', 'column']
        indexes = [
            models.Index(fields=['warehouse', 'row', 'column']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"R{self.row}-C{self.column}"
    
    @property
    def full_location(self):
        """إرجاع موقع كامل بصيغة سهلة القراءة"""
        return f"R{self.row}C{self.column}"
    
    def get_grid_position(self):
        """إرجاع الموضع في الشبكة للإحداثيات X,Y"""
        # الصف = Y (من الأعلى)
        # العمود = X (من اليسار)
        return {
            'x': self.column,
            'y': self.row
        }


class Product(models.Model):
    """نموذج المنتج - يمثل منتجاً في المستودع"""
    product_number = models.CharField(max_length=100, unique=True, verbose_name='رقم المنتج', db_index=True)
    name = models.CharField(max_length=200, verbose_name='اسم المنتج')
    category = models.CharField(max_length=100, blank=True, null=True, verbose_name='الفئة')
    description = models.TextField(blank=True, null=True, verbose_name='الوصف')
    
    # ربط المنتج بموقع واحد فقط
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, related_name='products', blank=True, null=True, verbose_name='الموقع')
    
    # معلومات الإضافة
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(0)], verbose_name='الكمية')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإضافة')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخر تحديث')
    
    class Meta:
        verbose_name = 'منتج'
        verbose_name_plural = 'المنتجات'
        ordering = ['product_number']
        indexes = [
            models.Index(fields=['product_number']),
            models.Index(fields=['name']),
            models.Index(fields=['location']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return f"{self.product_number} - {self.name}"
    
    def get_primary_location(self):
        """إرجاع الموقع الأساسي للمنتج"""
        return self.location


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('added', 'إضافة منتج'),
        ('updated', 'تعديل منتج'),
        ('deleted', 'حذف منتج'),
        ('quantity_taken', 'سحب كمية'),
        ('quantity_added', 'إضافة كمية'),
        ('location_assigned', 'ربط بالمواقع'),
        ('location_removed', 'إلغاء ربط موقع'),
    ]
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name='العملية')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='audit_logs', verbose_name='المنتج')
    product_number = models.CharField(max_length=50, verbose_name='رقم المنتج')
    quantity_before = models.IntegerField(null=True, blank=True, verbose_name='الكمية قبل')
    quantity_after = models.IntegerField(null=True, blank=True, verbose_name='الكمية بعد')
    quantity_change = models.IntegerField(default=0, verbose_name='التغيير')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    user = models.CharField(max_length=100, blank=True, default='System', verbose_name='المستخدم')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='التاريخ')
    
    class Meta:
        verbose_name = 'سجل عمليات'
        verbose_name_plural = 'سجلات العمليات'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['action']),
            models.Index(fields=['product']),
            models.Index(fields=['product_number']),
        ]
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.product_number} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class DailyReportArchive(models.Model):
    """نموذج لحفظ التقارير اليومية"""
    report_date = models.DateField(verbose_name='تاريخ التقرير', unique=True)
    hijri_date = models.CharField(max_length=100, verbose_name='التاريخ الهجري', blank=True)
    
    # الإحصائيات
    products_added = models.IntegerField(default=0, verbose_name='منتجات مضافة')
    products_updated = models.IntegerField(default=0, verbose_name='منتجات محدثة')
    products_deleted = models.IntegerField(default=0, verbose_name='منتجات محذوفة')
    quantities_taken = models.IntegerField(default=0, verbose_name='كميات مسحوبة')
    locations_assigned = models.IntegerField(default=0, verbose_name='مواقع مخصصة')
    total_added = models.IntegerField(default=0, verbose_name='إجمالي الكميات المضافة')
    total_removed = models.IntegerField(default=0, verbose_name='إجمالي الكميات المسحوبة')
    
    # بيانات JSON كاملة
    report_data = models.JSONField(verbose_name='بيانات التقرير', default=dict)
    
    # علامة للحفظ التلقائي
    is_auto_saved = models.BooleanField(default=False, verbose_name='حفظ تلقائي')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    
    class Meta:
        verbose_name = 'تقرير يومي محفوظ'
        verbose_name_plural = 'التقارير اليومية المحفوظة'
        ordering = ['-report_date']
        indexes = [
            models.Index(fields=['-report_date']),
        ]
    
    def __str__(self):
        return f"تقرير {self.report_date}"


class Order(models.Model):
    """نموذج لحفظ الطلبيات المسحوبة"""
    order_number = models.CharField(max_length=50, unique=True, verbose_name='رقم الطلبية', db_index=True)
    
    # معلومات الطلبية
    products_data = models.JSONField(verbose_name='بيانات المنتجات', default=list)
    total_products = models.IntegerField(default=0, verbose_name='عدد المنتجات')
    total_quantities = models.IntegerField(default=0, verbose_name='إجمالي الكميات المسحوبة')
    
    # معلومات إضافية
    recipient_name = models.CharField(max_length=200, blank=True, null=True, verbose_name='اسم المستلم')
    notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات')
    user = models.CharField(max_length=100, blank=True, default='System', verbose_name='المستخدم')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    
    class Meta:
        verbose_name = 'طلب مسحوب'
        verbose_name_plural = 'الطلبات المسحوبة'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['order_number']),
        ]
    
    def __str__(self):
        return f"طلب {self.order_number} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class ProductReturn(models.Model):
    """نموذج المرتجعات - تسجيل المرتجعات وإضافة الكميات للمنتجات"""
    return_number = models.CharField(max_length=50, unique=True, verbose_name='رقم المرتجع', db_index=True)
    
    # معلومات المرتجع
    products_data = models.JSONField(verbose_name='بيانات المنتجات المرتجعة', default=list)
    total_products = models.IntegerField(default=0, verbose_name='عدد المنتجات')
    total_quantities = models.IntegerField(default=0, verbose_name='إجمالي الكميات المرتجعة')
    
    # معلومات إضافية
    return_reason = models.CharField(max_length=200, blank=True, null=True, verbose_name='سبب الإرجاع')
    returned_by = models.CharField(max_length=200, blank=True, null=True, verbose_name='اسم المرسل')
    notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات')
    user = models.CharField(max_length=100, blank=True, default='System', verbose_name='المستخدم الذي أضاف المرتجع')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    
    class Meta:
        verbose_name = 'مرتجع'
        verbose_name_plural = 'المرتجعات'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['return_number']),
        ]
    
    def __str__(self):
        return f"مرتجع {self.return_number} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def get_total_value(self):
        """حساب إجمالي قيمة المرتجع (اختياري - إذا كان هناك أسعار)"""
        return self.total_quantities


# ========== نظام المستخدمين والصلاحيات ==========

class UserProfile(models.Model):
    """ملف المستخدم الشخصي - يربط User بمعلومات إضافية"""
    USER_TYPES = [
        ('admin', 'مسؤول'),
        ('staff', 'موظف'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_profile', verbose_name='المستخدم')
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='staff', verbose_name='نوع المستخدم')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='رقم الهاتف')
    notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    last_activity = models.DateTimeField(null=True, blank=True, verbose_name='آخر نشاط')
    last_login_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name='آخر IP تسجيل دخول')
    
    class Meta:
        verbose_name = 'ملف مستخدم'
        verbose_name_plural = 'ملفات المستخدمين'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['-last_activity']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_user_type_display()}"
    
    def is_admin(self):
        """التحقق من كون المستخدم مسؤول"""
        return self.user_type == 'admin' or self.user.is_superuser
    
    def is_staff_user(self):
        """التحقق من كون المستخدم موظف"""
        return self.user_type == 'staff'
    
    def can_access_maintenance(self):
        """التحقق من إمكانية الوصول لصفحات الصيانة"""
        return self.is_admin()
    
    def can_access_admin_dashboard(self):
        """التحقق من إمكانية الوصول للوحة تحكم المسؤول"""
        return self.is_admin()
    
    def update_activity(self, ip_address=None):
        """تحديث آخر نشاط"""
        self.last_activity = timezone.now()
        if ip_address:
            self.last_login_ip = ip_address
        self.save(update_fields=['last_activity', 'last_login_ip'])


class UserActivityLog(models.Model):
    """سجل أنشطة المستخدمين - تتبع شامل لجميع العمليات"""
    ACTION_TYPES = [
        ('login', 'تسجيل دخول'),
        ('logout', 'تسجيل خروج'),
        ('product_added', 'إضافة منتج'),
        ('product_updated', 'تعديل منتج'),
        ('product_deleted', 'حذف منتج'),
        ('product_viewed', 'عرض منتج'),
        ('order_created', 'إنشاء طلب'),
        ('order_viewed', 'عرض طلب'),
        ('order_deleted', 'حذف طلب'),
        ('location_assigned', 'ربط موقع'),
        ('location_updated', 'تعديل موقع'),
        ('quantity_taken', 'سحب كمية'),
        ('quantity_reset', 'تصفير كميات'),
        ('backup_created', 'إنشاء نسخة احتياطية'),
        ('backup_restored', 'استعادة نسخة احتياطية'),
        ('data_deleted', 'حذف بيانات'),
        ('user_created', 'إنشاء مستخدم'),
        ('user_updated', 'تعديل مستخدم'),
        ('user_deleted', 'حذف مستخدم'),
        ('page_viewed', 'عرض صفحة'),
        ('export_pdf', 'تصدير PDF'),
        ('export_excel', 'تصدير Excel'),
        ('search_performed', 'بحث'),
        ('other', 'أخرى'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs', verbose_name='المستخدم')
    action = models.CharField(max_length=50, choices=ACTION_TYPES, verbose_name='نوع العملية')
    description = models.CharField(max_length=500, verbose_name='الوصف')
    
    # معلومات إضافية
    object_type = models.CharField(max_length=100, blank=True, null=True, verbose_name='نوع الكائن')
    object_id = models.IntegerField(null=True, blank=True, verbose_name='معرف الكائن')
    object_name = models.CharField(max_length=200, blank=True, null=True, verbose_name='اسم الكائن')
    
    # تفاصيل العملية
    details = models.JSONField(default=dict, blank=True, verbose_name='التفاصيل')
    
    # معلومات الشبكة
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='عنوان IP')
    user_agent = models.TextField(blank=True, null=True, verbose_name='User Agent')
    
    # معلومات إضافية
    location = models.CharField(max_length=100, blank=True, null=True, verbose_name='الموقع')  # إذا كان مرتبط بموقع في المستودع
    url = models.CharField(max_length=500, blank=True, null=True, verbose_name='رابط الصفحة')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='التاريخ والوقت')
    
    class Meta:
        verbose_name = 'سجل نشاط مستخدم'
        verbose_name_plural = 'سجلات أنشطة المستخدمين'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action']),
            models.Index(fields=['object_type', 'object_id']),
            models.Index(fields=['ip_address']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    @classmethod
    def log_activity(cls, user, action, description, **kwargs):
        """طريقة مساعدة لتسجيل النشاط"""
        request = kwargs.get('request')
        details = kwargs.get('details', {})
        object_type = kwargs.get('object_type')
        object_id = kwargs.get('object_id')
        object_name = kwargs.get('object_name')
        location = kwargs.get('location')
        
        # استخراج معلومات من request إذا كان موجوداً
        ip_address = None
        user_agent = None
        url = None
        if request:
            ip_address = cls.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
            url = request.path
        
        # إنشاء السجل
        activity = cls.objects.create(
            user=user,
            action=action,
            description=description,
            object_type=object_type,
            object_id=object_id,
            object_name=object_name,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            url=url,
            location=location,
        )
        
        # تحديث آخر نشاط في UserProfile
        if hasattr(user, 'user_profile'):
            user.user_profile.update_activity(ip_address)
        
        return activity
    
    @staticmethod
    def get_client_ip(request):
        """الحصول على عنوان IP الحقيقي للعميل"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

