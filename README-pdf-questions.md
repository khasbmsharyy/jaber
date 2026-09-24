# إضافة أسئلة ملف الـ PDF إلى صفحة الويب

تمت إضافة صفحة `pdf-questions.html` وأداة `tools/extract_pdf_questions.py`.

## التشغيل

```bash
pip install -r requirements.txt
python tools/extract_pdf_questions.py "تمارين جبر خطي(2).pdf" pdf_questions.json
```

بعد إنشاء `pdf_questions.json` افتح `pdf-questions.html` عبر خادم محلي (لأن المتصفح يمنع `fetch` من `file://`):

```bash
python -m http.server 8000
```

ثم افتح `http://localhost:8000/pdf-questions.html`.

الأداة تحفظ رقم الصفحة وتصنف السؤال حسب عناوين/كلمات موضوع الجبر الخطي. إذا كان ملف الـPDF يحتوي على نص الحل، يمكن وضعه في حقل `solution` في ملف JSON ليظهر داخل بطاقة **الحل خطوة بخطوة**؛ أما ملفات PDF المصورة فتحتاج OCR قبل الاستخراج.
