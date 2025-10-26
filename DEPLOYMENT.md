# 🚀 دليل النشر - Found Inventory

## 📋 المتطلبات

### للبدء السريع (SQLite):
- ✅ Python 3.11+
- ✅ Django 4.2+

### للإنتاج مع PostgreSQL:
- ✅ Python 3.11+
- Django 4.2
- PostgreSQL 12+
- محرك ويب: Gunicorn أو uWSGI
- خادم ويب: Nginx (موصى به)

---

## 🔧 الإعداد (Development)

```bash
# 1. الانتقال للمجلد
cd C:\Users\ammar\OneDrive\Desktop\found-inventory

# 2. إنشاء وتفعيل البيئة الافتراضية (اختياري)
python -m venv venv
venv\Scripts\activate

# 3. تثبيت المتطلبات
pip install -r requirements.txt

# 4. إنشاء قاعدة البيانات
python manage.py migrate

# 5. إنشاء البيانات التجريبية
python manage.py create_sample_data

# 6. إنشاء حساب المدير
python manage.py createsuperuser

# 7. تشغيل الخادم
python manage.py runserver
```

---

## 🐘 التحول إلى PostgreSQL

### 1. تعديل settings.py

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'inventory_db',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 2. إنشاء قاعدة البيانات

```bash
psql -U postgres
CREATE DATABASE inventory_db;
\q
```

### 3. تشغيل Migrations

```bash
python manage.py migrate
python manage.py createsuperuser
```

---

## 🚢 النشر للإنتاج

### باستخدام Gunicorn + Nginx

#### 1. تثبيت Gunicorn

```bash
pip install gunicorn
```

#### 2. إنشاء ملف Gunicorn

`gunicorn_config.py`:

```python
bind = "0.0.0.0:8000"
workers = 4
timeout = 120
```

#### 3. تشغيل Gunicorn

```bash
gunicorn inventory_project.wsgi:application --config gunicorn_config.py
```

#### 4. إعداد Nginx

`/etc/nginx/sites-available/inventory`:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /static/ {
        alias /path/to/your/staticfiles/;
    }
    
    location /media/ {
        alias /path/to/your/media/;
    }
}
```

---

## 📦 التحسينات للإنتاج

### 1. تعطيل DEBUG

في `settings.py`:

```python
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']
```

### 2. إعداد ملفات الثابتة

```python
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

```bash
python manage.py collectstatic
```

### 3. استخدام قاعدة بيانات محسّنة

- استخدم PostgreSQL للإنتاج
- ضبط الاتصالات المناسبة
- تفعيل الـ caching

### 4. الأمان

```python
SECRET_KEY = config('SECRET_KEY')
DEBUG = False
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

---

## 🔒 متغيرات البيئة

أنشئ ملف `.env`:

```env
SECRET_KEY=your-super-secret-key-here
DEBUG=False
DB_NAME=inventory_db
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

---

## 📊 المراقبة والصيانة

### السجلات

```bash
# سجلات Gunicorn
tail -f logs/gunicorn.log

# سجلات Nginx
tail -f /var/log/nginx/access.log
```

### النسخ الاحتياطي

```bash
# نسخ احتياطي لقاعدة البيانات
python manage.py dumpdata > backup.json

# استعادة
python manage.py loaddata backup.json
```

---

## 🎯 نصائح الأداء

1. ✅ استخدم PostgreSQL بدلاً من SQLite للإنتاج
2. ✅ فعّل التخزين المؤقت (Redis/Memcached)
3. ✅ استخدم CDN للملفات الثابتة
4. ✅ ضع حد أقصى للـ workers في Gunicorn
4. ✅ راقب استخدام الذاكرة والأداء

---

## ✅ الاختبار

```bash
# اختبار URL
curl http://localhost:8000

# اختبار الـ API
curl http://localhost:8000/api/search/?numbers=BAG-001
```

---

النظام جاهز للإطلاق! 🚀

