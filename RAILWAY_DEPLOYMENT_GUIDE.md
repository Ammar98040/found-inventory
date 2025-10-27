# دليل النشر الكامل على Render مع PostgreSQL

## الخطوة 1: التسجيل في Render

1. اذهب إلى: https://dashboard.render.com/
2. اضغط على "Get Started for Free"
3. اختر "Sign up with GitHub"
4. اربط حسابك GitHub

**ملاحظة مهمة:** يطلب Render إدخال معلومات بطاقة ائتمانية للتسجيل، لكن الخطة المجانية تبقى مجانية دائماً ولن يتم خصم أي مبلغ.

---

## الخطوة 2: إنشاء قاعدة بيانات PostgreSQL

1. في dashboard Render، اضغط على **"+ New +"**
2. اختر **"PostgreSQL"**
3. أدخل:
   - **Name:** `found-inventory-db`
   - **Database:** `inventory_db`
   - **User:** `found_user`
   - **Plan:** **Free**
4. اختر **Region:** أقرب منطقة لك
5. اضغط **"Create Database"**

---

## الخطوة 3: إنشاء Web Service

1. اضغط على **"+ New +"** مرة أخرى
2. اختر **"Web Service"**
3. اختر **"Connect repository"** واختر مستودعك `Ammar98040/found-inventory`

---

## الخطوة 4: إعدادات Web Service

أدخل التالي:

### Basic Settings:
- **Name:** `found-inventory`
- **Region:** نفس منطقة قاعدة البيانات
- **Branch:** `main`

### Build & Deploy:
- **Root Directory:** (اتركه فارغ)
- **Environment:** `Python 3`

### Build Command:
```
pip install -r requirements.txt && python manage.py collectstatic --noinput
```

### Start Command:
```
gunicorn inventory_project.wsgi:application
```

---

## الخطوة 5: Environment Variables

في قسم **"Environment"**، أضف المتغيرات التالية:

| Key | Value |
|-----|-------|
| `SECRET_KEY` | `r#$*ui1pee6vd_rx5u(idpztm*c@^2bx$@&k1q2_l=1_0%7hen` |
| `DEBUG` | `False` |
| `DB_NAME` | `inventory_db` |
| `DB_USER` | `found_user` |
| `DB_PASSWORD` | **انسخه من صفحة PostgreSQL** |
| `DB_HOST` | **انسخه من صفحة PostgreSQL (ending with .on.render.com)** |
| `DB_PORT` | `5432` |

**كيف تجد معلومات PostgreSQL؟**
1. افتح صفحة قاعدة البيانات PostgreSQL
2. في قسم **"Connections"** ستجد:
   - **Internal Database URL:** يحتوي على جميع المعلومات

مثال:
```
postgres://found_user:password@dpg-xxxxx-a.frankfurt-postgres.render.com/inventory_db
```

من هذا الرابط:
- `found_user` = DB_USER
- `password` = DB_PASSWORD
- `dpg-xxxxx-a.frankfurt-postgres.render.com` = DB_HOST
- `inventory_db` = DB_NAME

---

## الخطوة 6: ربط Web Service بقاعدة البيانات

1. في صفحة **Web Service**، اذهب إلى **"Settings"**
2. في قسم **"Connections"**
3. اختر **"Add Connection"**
4. اختر `found-inventory-db`
5. Render سيضيف متغيرات البيئة تلقائياً

---

## الخطوة 7: Deploy

1. اضغط على **"Create Web Service"**
2. Render ستبدأ عملية البناء والنشر
3. انتظر حتى ترى **"Live"** بجانب عنوان URL

---

## الخطوة 8: إعداد قاعدة البيانات

بعد النشر، يجب تشغيل migrations:

1. افتح صفحة Web Service
2. اذهب إلى **"Shell"**
3. في terminal الذي يفتح، اكتب:

```bash
python manage.py migrate
```

---

## الخطوة 9: الوصول للنظام

- ستحصل على رابط مثل: `found-inventory-xxxx.onrender.com`
- افتح الرابط في المتصفح
- النظام الآن جاهز للاستخدام!

---

## نصائح مهمة:

1. **الخطة المجانية على Render:**
   - تستيقظ عند الطلب (قد يستغرق 30-60 ثانية في المرة الأولى)
   - تحصل على 750 ساعة شهرياً

2. **لتجنب الاستيقاظ البطيء:**
   - يمكن تفعيل **"Health Check"** في الإعدادات
   - سيحافظ على الخدمة نشطة

3. **النسخ الاحتياطي:**
   - استخدم ميزة **"Backup and Restore"** في قاعدة البيانات

---

## حل المشاكل الشائعة:

### المشكلة: "Application Error"
**الحل:** تحقق من Logs:
1. افتح Web Service
2. افتح تبويب **"Logs"**
3. ابحث عن الأخطاء

### المشكلة: "Database connection failed"
**الحل:** 
- تأكد من صحة Environment Variables
- تأكد من أن Service مربوط بقاعدة البيانات

### المشكلة: "Static files not loading"
**الحل:**
- تأكد من تشغيل `python manage.py collectstatic --noinput` في Build Command

---

## دعم إضافي:

- **Render Docs:** https://render.com/docs
- **Django on Render:** https://render.com/docs/deploy-django

**بالتوفيق! 🚀**
