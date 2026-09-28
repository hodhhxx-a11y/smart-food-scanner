ماسح الوجبات الذكي - طريقة التشغيل

1) فك الضغط عن المجلد.
2) افتح الطرفية داخل المجلد ونفّذ:
   pip install -r requirements.txt
   streamlit run app.py

المفتاح موجود في:  .streamlit/secrets.toml   (لا ترفع هذا الملف على GitHub، وهو مُضاف في .gitignore)
كود الإعلان موجود في app.py داخل المتغير AD_HTML.

على Streamlit Cloud: ارفع app.py و requirements.txt و .streamlit/config.toml فقط،
ثم الصق السطر التالي في Settings > Secrets:
   GEMINI_API_KEY = "مفتاحك"
