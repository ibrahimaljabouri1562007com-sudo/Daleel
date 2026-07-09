# مركز الدليل — Al‑Daleel Center

موقع **مركز الدليل** للتدريب والاستشارات الإنسانية — نسخة أوّلية (Prototype) مبنية بـ **Python + Flask**،
عربية بالكامل (RTL)، مع **لوحة مشرف** لإدارة المحتوى دون تعديل الشيفرة.

A bilingual‑ready, right‑to‑left Arabic website for Al‑Daleel Center, built with Flask, featuring
an admin edit mode to publish/modify/reorder content (books, videos, articles, news) with no code.

---

## ✨ الميزات / Features
- صفحات: الرئيسية، مدير المركز، مكتبتنا الرقمية (فيديوهات/مقالات/كتيبات)، اتصل بنا.
- **وضع المشرف (Edit mode):** إضافة/تعديل/حذف + سحب لإعادة الترتيب، لكل قسم.
- نشر فيديوهات (رابط YouTube/Vimeo يُعرض داخل الصفحة، أو ملف)، صور غلاف، ومقالات بمنسّق نصوص بسيط.
- قسم «جديدنا» في الصفحة الرئيسية قابل للتحرير.
- حماية: كل إجراءات التحرير خلف **تسجيل دخول المشرف** (كلمة مرور واحدة).

## 🧰 المتطلبات / Requirements
- Python 3.10+ (تم الاختبار على 3.12)
- Flask (انظر `requirements.txt`)

## ▶️ التشغيل محليًا / Run locally
```bash
# 1) (اختياري) بيئة افتراضية
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 2) تثبيت المتطلبات
pip install -r requirements.txt

# 3) التشغيل
python app.py
```
ثم افتح المتصفح على: **http://127.0.0.1:5000**

> عند أول تشغيل يُنشأ ملف قاعدة البيانات `daleel.db` تلقائيًا ويُملأ بمحتوى أولي.

## 🔐 دخول المشرف / Admin login
- الرابط: `/admin/login` (أو زر **دخول المشرف** أسفل الصفحة).
- كلمة المرور الافتراضية للتطوير: `daleel2026`.
- **لتغيير كلمة المرور** (موصى به قبل النشر) عيّن متغيّر البيئة قبل التشغيل:
```bash
# Windows PowerShell:
$env:ADMIN_PASSWORD="your-strong-password"
$env:SECRET_KEY="some-long-random-string"
python app.py
```

## 📁 البنية / Project structure
```
Daleel/
├── app.py              # التطبيق (المسارات + المنطق)
├── templates/          # صفحات HTML (Jinja) + لوحة المشرف
├── static/             # css · js · assets · uploads (ملفات المشرف)
├── requirements.txt    # المكتبات المطلوبة
├── .gitignore
└── daleel.db           # قاعدة البيانات (تُنشأ تلقائيًا — غير مرفوعة)
```

## 📝 ملاحظات / Notes
- قاعدة البيانات (`daleel.db`) والملفات المرفوعة (`static/uploads/`) **محلية** ولا تُرفع إلى Git.
- المشروع نموذج أوّلي؛ الموقع المباشر الأصلي منفصل ولا يتأثّر.
