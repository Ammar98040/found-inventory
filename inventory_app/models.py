from django.db import models
from django.core.validators import MinValueValidator


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

