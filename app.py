import hashlib
import html
import io
import time

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai import types
from PIL import Image
from pydantic import BaseModel

# ----------------------------------------------------------------------------
# الإعدادات العامة للموقع
# ----------------------------------------------------------------------------
MODEL_NAME = "gemini-3.8-flash"
WAIT_SECONDS = 6

st.set_page_config(
    page_title="ماسح الوجبات الذكي",
    page_icon="🥗",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ----------------------------------------------------------------------------
# التصميم الجمالي المطور والفني (CSS)
# ----------------------------------------------------------------------------
CSS = """
<style>
@import url('https://googleapis.com');

:root {
  --ink: #12262a;
  --muted: #5b6f73;
  --line: #dfe7e6;
  --bg: #f4f7f6;
  --panel: #ffffff;
  --spruce: #1f6f5c;
  --spruce-dark: #17564a;
  --cal: #e8801f;
  --protein: #3a7fc1;
  --fat: #d9695f;
  --carb: #d8a92f;
}

html, body, [class*="st-"], .stApp, button, input {
  font-family: 'IBM Plex Sans Arabic', 'Segoe UI', Tahoma, sans-serif !important;
}
.stApp { background: var(--bg); color: var(--ink); }
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent; height: 0; }
.block-container { direction: rtl; text-align: right; max-width: 640px; padding-top: 1.6rem; padding-bottom: 3rem; }

/* تصميم الترويسة والبراند */
.brand { display: flex; align-items: center; gap: .6rem; margin-bottom: .2rem; }
.brand-mark { width: 38px; height: 38px; border-radius: 11px; background: var(--spruce);
  display: flex; align-items: center; justify-content: center; font-size: 20px; }
.brand-name { font-size: 1.45rem; font-weight: 700; color: var(--ink); }
.tagline { color: var(--muted); margin: .25rem 0 1.4rem; font-size: .98rem; line-height: 1.8; }

/* التبويبات وعناصر الإدخال والرفع */
[data-baseweb="tab-list"] { gap: .4rem; background: #e9efee; padding: 4px; border-radius: 12px; }
[data-baseweb="tab"] { border-radius: 9px; height: 42px; padding: 0 1rem; font-weight: 600; color: var(--muted); }
[data-baseweb="tab"][aria-selected="true"] { background: var(--panel); color: var(--ink); box-shadow: 0 1px 3px rgba(18,38,42,.12); }
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display: none; }
[data-testid="stCameraInput"] video, [data-testid="stCameraInput"] img, [data-testid="stImage"] img {
  border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
[data-testid="stFileUploaderDropzone"] { background: var(--panel); border: 1.5px dashed #b6c8c5; border-radius: 16px; padding: 1.6rem; }
[data-testid="stFileUploaderDropzone"]:hover { border-color: var(--spruce); }

/* العداد التنازلي التلقائي */
.cd-wrap { display: flex; align-items: center; gap: 1.1rem; background: var(--panel); border: 1px solid var(--line);
  border-radius: 18px; padding: 1.1rem 1.2rem; margin: 1rem 0; box-shadow: 0 2px 8px rgba(0,0,0,0.02); }
.cd-ring { width: 64px; height: 64px; border-radius: 50%; background: #eef6f3; flex: none; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; font-weight: 700; color: var(--spruce); }
.cd-title { font-weight: 600; font-size: 1.05rem; color: var(--ink); }
.cd-sub { color: var(--muted); font-size: .9rem; margin-top: .15rem; }

/* بطاقة عرض النتائج الفنية */
.result-card { background: var(--panel); border: 1px solid var(--line); border-radius: 20px; padding: 1.5rem; margin-top: 1.5rem; box-shadow: 0 4px 20px rgba(0,0,0,0.03); }
.meal-title { font-size: 1.6rem; font-weight: 700; color: var(--spruce); margin: 0 0 .2rem 0; }
.meal-subtitle { color: var(--muted); font-size: .85rem; margin-bottom: 1.2rem; }
.kcal-box { display: flex; align-items: baseline; gap: .4rem; margin-bottom: 1.2rem; }
.kcal-large { font-size: 3.4rem; font-weight: 700; color: var(--cal); line-height: 1; }
.kcal-lbl { color: var(--muted); font-weight: 500; font-size: .95rem; }

/* تصميم الجدول المنظم */
table.nutri-table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
table.nutri-table th { text-align: right; color: var(--muted); font-weight: 500; font-size: .85rem; padding: .6rem .4rem; border-bottom: 1.5px solid var(--line); }
table.nutri-table td { padding: .9rem .4rem; border-bottom: 1px solid var(--line); text-align: right; font-size: 1rem; }
table.nutri-table tr:last-child td { border-bottom: 0; }
table.nutri-table td.bold-val { font-weight: 700; color: var(--ink); }

.tip-box { margin-top: 1.4rem; padding: 1rem 1.1rem; background: #eef6f3; border-right: 4px solid var(--spruce); border-radius: 0 12px 12px 0; line-height: 1.8; font-size: .98rem; }
.tip-box b { color: var(--spruce-dark); }
.ad-header { color: var(--muted); font-size: .8rem; margin: .8rem 0 .3rem 0; font-weight: 500; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# تشغيل كود الإعلانات المدمج (Popunder في الخلفية)
# ----------------------------------------------------------------------------
ad_popunder = """
<script src="https://profitableratecpmnetwork.com"></script>
"""
components.html(ad_popunder, height=0, width=0)
# ----------------------------------------------------------------------------
# شكل النتيجة المطلوبة من Gemini
# ----------------------------------------------------------------------------
class MealAnalysis(BaseModel):
    is_food: bool
    meal_name: str
    calories: float
    protein_g: float
    fat_g: float
    carbs_g: float
    health_tip: str


PROMPT = """أنت خبير تغذية. حلل صورة الوجبة المرفقة وقدّر القيم الغذائية للحصة الظاهرة في الصورة.
- إذا لم تكن الصورة تحتوي على طعام اجعل is_food = false وضع 0 في القيم الرقمية.
- meal_name: اسم الوجبة التقريبي بالعربية.
- calories: السعرات الحرارية (kcal).
- protein_g: البروتين بالجرام.
- fat_g: الدهون بالجرام.
- carbs_g: الكربوهيدرات بالجرام.
- health_tip: نصيحة صحية سريعة في جملة أو جملتين بالعربية.
هذه تقديرات تقريبية."""


# ----------------------------------------------------------------------------
# الدوال المساعدة
# ----------------------------------------------------------------------------
@st.cache_resource
def get_client() -> genai.Client:
    return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])


def prepare_image(image_bytes: bytes) -> bytes:
    img = Image.open(io.BytesIO(image_bytes))
    img = img.convert("RGB")
    img.thumbnail((1280, 1280))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def analyze_meal(image_bytes: bytes) -> MealAnalysis:
    client = get_client()
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            types.Part.from_bytes(data=prepare_image(image_bytes), mime_type="image/jpeg"),
            PROMPT,
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=MealAnalysis,
            temperature=0.2,
        ),
    )
    return MealAnalysis.model_validate_json(response.text)


def run_countdown():
    title_box = st.empty()
    timer_box = st.empty()
    bar = st.progress(0)

    for remaining in range(WAIT_SECONDS, 0, -1):
        timer_box.markdown(
            f'<div class="cd-wrap">'
            f'<div class="cd-ring">{remaining}</div>'
            f'<div><div class="cd-title">جاري معالجة وتجهيز صورة الوجبة...</div>'
            f'<div class="cd-sub">سيبدأ التحليل تلقائياً خلال {remaining} ثوانٍ</div></div>'
            f'</div>',
            unsafe_allow_html=True
        )
        bar.progress((WAIT_SECONDS - remaining + 1) / WAIT_SECONDS)
        time.sleep(1)

    for box in (title_box, timer_box, bar):
        box.empty()


def show_result(result: MealAnalysis):
    if not result.is_food:
        st.warning("لم أتمكن من العثور على طعام في الصورة. جرّب صورة أوضح للوجبة.")
        return

    # عرض النتيجة بداخل قالب تصميم فني متناسق وأنيق
    html_layout = f"""
    <div class="result-card">
        <h2 class="meal-title">{result.meal_name}</h2>
        <div class="meal-subtitle">تحليل تقريبي للمكونات الغذائية والحصة الظاهرة</div>
        <div class="kcal-box">
            <span class="kcal-large">{result.calories:.0f}</span>
            <span class="kcal-lbl">سعرة حرارية</span>
        </div>
        <table class="nutri-table">
            <thead>
                <tr>
                    <th>العنصر الغذائي</th>
                    <th>الكمية بالجرام</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>البروتين</td>
                    <td class="bold-val" style="color: #3a7fc1;">{result.protein_g:.1f} جم</td>
                </tr>
                <tr>
                    <td>الدهون الإجمالية</td>
                    <td class="bold-val" style="color: #d9695f;">{result.fat_g:.1f} جم</td>
                </tr>
                <tr>
                    <td>الكربوهيدرات</td>
                    <td class="bold-val" style="color: #d8a92f;">{result.carbs_g:.1f} جم</td>
                </tr>
            </tbody>
        </table>
        <div class="tip-box">
            <b>💡 توجيه صحي:</b> {result.health_tip}
        </div>
    </div>
    """
    st.markdown(html_layout, unsafe_allow_html=True)
    st.caption("⚠️ القيم تقديرية مبنية على الذكاء الاصطناعي ولا تغني عن استشارة الطبيب.")


# ----------------------------------------------------------------------------
# الواجهة الرسومية المحسنة
# ----------------------------------------------------------------------------
st.markdown(
    '<div class="brand"><div class="brand-mark">🥗</div>'
    '<div class="brand-name">ماسح الوجبات الذكي</div></div>'
    '<div class="tagline">التقط صورة حية لوجبتك أو ارفعها من المعرض، وسيتولى الذكاء الاصطناعي تحليل قيمتها الغذائية فوراً.</div>',
    unsafe_allow_html=True
)

# عرض إعلان بنر مرئي مدمج بكود الحساب الخاص بك لضمان الأرباح الفورية
st.markdown('<div class="ad-header">📢 راعي خادم السيرفر:</div>', unsafe_allow_html=True)
my_native_ad = """
<script async="async" data-cfasync="false" src="https://pl31544583.profitableratecpmnetwork.com/0392b334f94fb470d7d8a56c8a5a4f67/invoke.js"></script>
<div id="container-0392b334f94fb470d7d8a56c8a5a4f67"></div>
"""
components.html(my_native_ad, height=200)
st.markdown("---")

tab_camera, tab_upload = st.tabs(["📷 الكاميرا الذكية", "🖼️ الرفع من المعرض"])

with tab_camera:
    camera_file = st.camera_input("التقط صورة للوجبة")

with tab_upload:
    uploaded_file = st.file_uploader("اختر ملف الصورة من جهازك", type=["jpg", "jpeg", "png", "webp"])

image_file = camera_file or uploaded_file

if image_file is not None:
    image_bytes = image_file.getvalue()
    image_hash = hashlib.md5(image_bytes).hexdigest()

    st.image(image_bytes, caption="الصورة التي سيتم تحليلها", use_container_width=True)

    if st.session_state.get("last_hash") != image_hash:
        st.session_state["last_hash"] = image_hash
        st.session_state.pop("result", None)
        st.session_state.pop("error", None)

        run_countdown()

        with st.spinner("🤖 جاري تحليل مكونات الصورة بواسطة Gemini..."):
            try:
                st.session_state["result"] = analyze_meal(image_bytes)
            except Exception as e:
                st.session_state["error"] = str(e)

    if "result" in st.session_state:
        show_result(st.session_state["result"])
    elif "error" in st.session_state:
        st.error("حدث خطأ أثناء الاتصال بالخادم. يرجى التحقق وإعادة المحاولة.")
        st.code(st.session_state["error"])
else:
    st.session_state.pop("last_hash", None)
