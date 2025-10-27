# دليل النشر الكامل على Fly.io - مجاني بدون بطاقة ائتمانية

## مزايا Fly.io:
✅ مجاني بالكامل  
✅ بدون بطاقة ائتمانية  
✅ يستضيف Django + PostgreSQL  
✅ مساحة 3GB  
✅ رابط واحد: `https://found-inventory.fly.dev`  
✅ سريع ومستقر  

---

## الخطوة 1: تثبيت Fly.io CLI

### Windows (PowerShell):
```powershell
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

### إعادة تشغيل PowerShell بعد التثبيت

---

## الخطوة 2: التسجيل في Fly.io

1. افتح PowerShell
2. اكتب:
```powershell
fly auth signup
```
3. سيُفتح المتصفح تلقائياً
4. اختر "Sign up with GitHub"
5. اربط حسابك GitHub
6. **لا حاجة لبطاقة ائتمانية!**

---

## الخطوة 3: إنشاء PostgreSQL Database

في نفس PowerShell:

```powershell
# إنشاء قاعدة بيانات PostgreSQL (3GB مجاناً)
fly postgres create --name found-inventory-db --region iad --vm-size shared-cpu-1x --volume-size 3
```

**انتظر** حتى ينتهي الإنشاء (دقيقتان).

---

## الخطوة 4: ربط قاعدة البيانات بالتطبيق

```powershell
# الانتقال إلى مجلد المشروع
cd C:\Users\ammar\OneDrive\Desktop\found-inventory

# ربط قاعدة البيانات بالتطبيق
fly postgres attach --app found-inventory found-inventory-db
```

---

## الخطوة 5: إعداد متغيرات البيئة

```powershell
# إضافة SECRET_KEY
fly secrets set SECRET_KEY="r#$*ui1pee6vd_rx5u(idpztm*c@^2bx$@&k1q2_l=1_0%7hen"

# إضافة DEBUG
fly secrets set DEBUG="False"
```

---

## الخطوة 6: رفع المشروع إلى Fly.io

```powershell
# أول مرة
fly launch

# عند السؤال:
# App name: found-inventory
# Database: ظهر بعد ربط PostgreSQL (اختار "found-inventory-db")
# Select region: iad (1)

# سيُسأل:
# Would you like to setup a Postgresql database now? No (لأننا أنشأناه بالفعل)
# Would you like to deploy now? No (سننشر يدوياً)
```

---

## الخطوة 7: تشغيل Migrations

```powershell
# تشغيل migrations على قاعدة البيانات
fly ssh console
```

داخل الـ console:

```bash
python manage.py migrate
python manage.py createsuperuser
exit
```

---

## الخطوة 8: النشر النهائي

```powershell
# العودة من SSH
exit

# النشر
fly deploy
```

**انتظر** حتى ينتهي النشر (3-5 دقائق).

---

## الخطوة 9: الوصول للنظام

بعد النشر، ستحصل على رابط مثل:
```
https://found-inventory.fly.dev
```

افتح الرابط في المتصفح!

---

## ميزات النظام على Fly.io:

1. **رابط دائم**: `https://found-inventory.fly.dev`
2. **قاعدة بيانات منفصلة**: PostgreSQL 3GB
3. **تحديث تلقائي**: عند `git push`
4. **HTTPS مجاني**: شهادة SSL تلقائية
5. **سرعة عالية**: خوادم سريعة

---

## كيفية إجراء تحديثات:

### الطريقة 1: من GitHub (تلقائي)
```powershell
git add .
git commit -m "Update"
git push origin main
fly deploy  # نشر على Fly.io
```

### الطريقة 2: مباشرة من الملفات
```powershell
git add .
git commit -m "Update"
fly deploy
```

---

## إعادة تشغيل النظام:

```powershell
fly apps restart found-inventory
```

---

## عرض Logs (للأخطاء):

```powershell
fly logs
```

---

## تحديث قاعدة البيانات:

```powershell
fly ssh console
python manage.py migrate
exit
```

---

## معلومات مهمة:

### ✅ المجاني في Fly.io:
- 3 Compute VMs (آلات افتراضية)
- 3GB Storage للملفات
- 3GB PostgreSQL Database
- Traffic (مرور) مجاني غير محدود
- HTTPS مجاني

### ⚠️ ملاحظات:
1. **نوم التطبيق**: إذا لم يُستخدم لمدة ساعة، ينام تلقائياً
2. **استيقاظ سريع**: عند أول طلب، يستيقظ خلال 5-10 ثواني
3. **لتجنب النوم**: اشترِ "Always On" (~$2/شهر) - اختياري

---

## حل المشاكل:

### المشكلة: "Error: failed to fetch an image or build"
**الحل:**
```powershell
fly deploy --remote-only
```

### المشكلة: "Database connection failed"
**الحل:**
```powershell
fly postgres connect --app found-inventory found-inventory-db
```

### المشكلة: "App not responding"
**الحل:**
```powershell
fly logs
fly apps restart found-inventory
```

---

## إحصائيات الاستخدام:

```powershell
# عرض استخدام الخدمة
fly status
fly scale show
```

---

## حذف التطبيق (إذا أردت):

```powershell
# تحذير: سيتم حذف كل شيء!
fly apps destroy found-inventory
```

---

## دعم إضافي:

- **Fly.io Docs**: https://fly.io/docs
- **Django on Fly**: https://fly.io/docs/languages-and-frameworks/python/
- **Community**: https://community.fly.io/

---

**بالتوفيق! 🚀**

الآن نظامك متاح على: `https://found-inventory.fly.dev`
