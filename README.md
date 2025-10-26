# 📦 نظام إدارة المستودع - Found Inventory

نظام ذكي لإدارة المستودعات وإيجاد المنتجات فوراً من خلال البحث برقم المنتج.

---

## 🌟 الميزات

- ✅ **بحث متعدد وسريع**: ابحث عن أكثر من 15 منتج في نفس اللحظة
- ✅ **خرائط تفاعلية**: عرض مواقع المنتجات على خريطة المستودع
- ✅ **نظام إحداثيات**: تتبع دقيق لموقع كل منتج
- ✅ **واجهة عربية جذابة**: تصميم عصري ومتجاوب
- ✅ **إدارة سهلة**: لوحة تحكم شاملة لإدارة المنتجات والأماكن

---

## 🛠️ التقنيات المستخدمة

- **Backend**: Python 3.11 + Django 4.2
- **Database**: SQLite (للبدء السريع) / PostgreSQL (للإنتاج)
- **Frontend**: HTML5 + CSS3 + JavaScript (Vanilla)
- **Real-time Search**: AJAX

---

## 🚀 البدء السريع

### الطريقة الأسهل (Windows):

```bash
# فقط اضغط نقرتين على الملف
start.bat
```

### الطريقة اليدوية:

```bash
# 1. الانتقال للمجلد
cd C:\Users\ammar\OneDrive\Desktop\found-inventory

# 2. إنشاء حساب المدير
python manage.py createsuperuser

# 3. تشغيل الخادم
python manage.py runserver
```

### البيانات التجريبية:

تم إنشاء 15 منتج و 64 موقع تلقائياً! ✅

---

## 📖 دليل الاستخدام

### 1. الصفحة الرئيسية

افتح http://localhost:8000 وأدخل أرقام المنتجات:

```
BAG-001
BAG-002
BAG-003
```

ثم اضغط "بحث" ⚡

### 2. لوحة الإدارة

افتح http://localhost:8000/admin

- إضافة مستودعات جديدة
- إدارة الأماكن والإحداثيات
- إضافة/تعديل المنتجات
- ربط المنتجات بالأماكن

### 3. أمثلة الأرقام المتاحة:

```
BAG-001 إلى BAG-015
```

---

## 📁 هيكل المشروع

```
found-inventory/
├── inventory_project/      # إعدادات Django
├── inventory_app/          # التطبيق الرئيسي
│   ├── models.py          # النماذج (Warehouse, Location, Product)
│   ├── views.py           # منطق البحث والـ API
│   ├── admin.py           # إدارة Django
│   └── management/        # أوامر خاصة
├── templates/              # قوالب HTML
├── static/                 # CSS و JavaScript
│   ├── css/style.css
│   └── js/main.js
├── requirements.txt        # المتطلبات
└── README.md              # هذا الملف
```

---

## 🔧 الإعداد المتقدم

### التحول إلى PostgreSQL:

1. عدّل `inventory_project/settings.py`
2. أنشئ قاعدة بيانات
3. شغّل migrations

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

للتفاصيل الكاملة، راجع: `DEPLOYMENT.md`

---

## 📚 الوثائق

- 📄 `QUICK_START.md` - دليل البدء السريع
- 📄 `SETUP.md` - دليل الإعداد الكامل
- 📄 `DEPLOYMENT.md` - دليل النشر للإنتاج

---

## 🎯 حالات الاستخدام

### للمستودعات:
- البحث الفوري عن مواقع 150+ منتج
- تتبع دقيق للإحداثيات
- خرائط تفاعلية للمستودع

### للموظفين:
- واجهة عربية بسيطة
- بحث سريع بدون تعقيد
- نتائج واضحة مع خرائط

---

## 🐛 استكشاف الأخطاء

### المشكلة: لا يفتح المتصفح

```bash
# تأكد من أن الخادم يعمل
python manage.py runserver

# جرب رابط آخر
http://127.0.0.1:8000
```

### المشكلة: لا توجد بيانات

```bash
# أنشئ بيانات تجريبية
python manage.py create_sample_data
```

### المشكلة: قاعدة البيانات

```bash
# إعادة إنشاء قاعدة البيانات
python manage.py migrate
python manage.py migrate inventory_app --run-syncdb
```

---

## ⚡ الأداء

- **سرعة البحث**: أقل من 200ms لمئات المنتجات
- **دعم متعدد**: ابحث عن 50+ منتج في نفس الوقت
- **خرائط ديناميكية**: تحديث فوري للمواقع

---

## 🤝 المساهمة

مرحب بك لتحسين المشروع! يمكنك:
- إضافة ميزات جديدة
- تحسين الواجهة
- تحسين الأداء
- إصلاح الأخطاء

---

## 📝 الترخيص

هذا المشروع مجاني ومفتوح المصدر.

---

## 🎉 ابدأ الآن!

```bash
python manage.py createsuperuser
python manage.py runserver
```

ثم افتح: http://localhost:8000

---

**Made with ❤️ using Django**

