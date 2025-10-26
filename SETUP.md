# دليل الإعداد السريع - Found Inventory

## ⚡ الإعداد السريع بدون PostgreSQL

إذا كنت تريد البدء بسرعة بدون إعداد PostgreSQL، يمكنك استخدام SQLite:

### 1. تعديل إعدادات قاعدة البيانات

افتح ملف `inventory_project/settings.py` وابحث عن سطر `DATABASES` واستبدله بـ:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### 2. تشغيل المشروع

```bash
# إنشاء الجداول
python manage.py migrate

# إنشاء حساب مدير
python manage.py createsuperuser

# تشغيل الخادم
python manage.py runserver
```

---

## 🐘 الإعداد مع PostgreSQL

### 1. تثبيت PostgreSQL

- حمّل من: https://www.postgresql.org/download/windows/
- أو استخدم Chocolatey: `choco install postgresql`

### 2. إنشاء قاعدة البيانات

```bash
# افتح psql
psql -U postgres

# داخل psql
CREATE DATABASE inventory_db;
\q
```

### 3. إعداد ملف البيئة

أنشئ ملف `.env` من `.env.example`:

```bash
cp .env.example .env
```

عدّل ملف `.env`:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=inventory_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

### 4. تشغيل المشروع

```bash
# إنشاء الجداول
python manage.py migrate

# إنشاء حساب مدير
python manage.py createsuperuser

# تشغيل الخادم
python manage.py runserver
```

---

## 📝 إضافة بيانات تجريبية

بعد تسجيل الدخول إلى لوحة الإدارة:

1. اذهب إلى: http://localhost:8000/admin
2. أدخل معلومات تسجيل الدخول
3. أضف مستودع جديد
4. أضف أماكن للمستودع (sections, rows, shelves)
5. أضف منتجات وربطها بالأماكن

---

## 🚀 البدء الفوري

افتح terminal وقم بالتالي:

```bash
# الانتقال لمجلد المشروع
cd C:\Users\ammar\OneDrive\Desktop\found-inventory

# استخدام SQLite (الأسرع)
# عدّل settings.py أولاً (انظر أعلاه)

# إنشاء البيانات
python manage.py migrate

# إنشاء مستخدم
python manage.py createsuperuser

# تشغيل
python manage.py runserver
```

ثم افتح المتصفح على: http://localhost:8000

