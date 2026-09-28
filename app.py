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
# التصميم الجمالي والفني المطور بالكامل (CSS)
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
.brand-mark { width: 42px; height: 42px; border-radius: 12px; background: var(--spruce);
  display: flex; align-items: center; justify-content: center; font-size: 22px; box-shadow: 0 4px 10px rgba(31,111,92,0.2); }
.brand-name { font-size: 1.55rem; font-weight: 700; color: var(--ink); }
.tagline { color: var(--muted); margin: .3rem 0 1.5rem; font-size: .98rem; line-height: 1.8; }

/* 🌟 تظبيط أزرار التبويبات الفنية الفخمة لتفادي الاختفاء والتداخل مع الإعلان */
[data-baseweb="tab-list"] { gap: .6rem; background: #e2ebe9; padding: 6px; border-radius: 14px; margin-top: 1rem; margin-bottom: 1.2rem; }
[data-baseweb="tab"] { border-radius: 10px; height: 46px; padding: 0 1.2rem; font-weight: 700; color: var(--muted); border: none !important; transition: all 0.2s ease-in-out; }
[data-baseweb="tab"][aria-selected="true"] { background: var(--spruce); color: #ffffff !important; box-shadow: 0 4px 12px rgba(31,111,92,0.25); }
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display: none; }

/* 📸 تظبيط مساحات عرض الصورة والكاميرا الاحترافية */
[data-testid="stCameraInput"] { border: 2px solid var(--line); border-radius: 20px; padding: 10px; background: var(--panel); box-shadow: 0 4px 15px rgba(0,0,0,0.02); }
[data-testid="stCameraInput"] video, [data-testid="stCameraInput"] img, [data-testid="stImage"] img {
  border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.04); border: 1px solid var(--line); }
[data-testid="stFileUploaderDropzone"] { background: var(--panel); border: 2px dashed #b6c8c5; border-radius: 20px; padding: 2rem 1.5rem; text-align: center; }
[data-testid="stFileUploaderDropzone"]:hover { border-color: var(--spruce); background: #fbfdfb; }

/* العداد التنازلي التلقائي الجميل */
.cd-wrap { display: flex; align-items: center; gap: 1.1rem; background: var(--panel); border: 1px solid var(--line);
  border-radius: 18px; padding: 1.1rem 1.2rem; margin: 1rem 0; box-shadow: 0 2px 8px rgba(0,0,0,0.02); }
.cd-ring { width: 64px; height: 64px; border-radius: 50%; background: #eef6f3; flex: none; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; font-weight: 700; color: var(--spruce); }
.cd-title { font-weight: 600; font-size: 1.05rem; color: var(--ink); }
.cd-sub { color: var(--muted); font-size: .9rem; margin-top: .15rem; }

/* بطاقة عرض النتائج الفنية الفاخرة */
.result-card { background: var(--panel); border: 1px solid var(--line); border-radius: 22px; padding: 1.6rem; margin-top: 1.5rem; box-shadow: 0 6px 24px rgba(0,0,0,0.03); border-right: 5px solid var(--spruce); }
.meal-title { font-size: 1.7rem; font-weight: 700; color: var(--spruce-dark); margin: 0 0 .2rem 0; }
.meal-subtitle { color: var(--muted); font-size: .88rem; margin-bottom: 1.3rem; }
.kcal-box { display: flex; align-items: baseline; gap: .4rem; margin-bottom: 1.2rem; }
.kcal-large { font-size: 3.6rem; font-weight: 700; color: var(--cal); line-height: 1; }
.kcal-lbl { color: var(--muted); font-weight: 600; font-size: .95rem; }

/* تصميم الجدول المنظم المودرن */
table.nutri-table { width: 100%; border-collapse: collapse; margin-top: 1.2rem; }
table.nutri-table th { text-align: right; color: var(--muted); font-weight: 600; font-size: .88rem; padding: .6rem .4rem; border-bottom: 2px solid var(--line); }
table.nutri-table td { padding: 1rem .4rem; border-bottom: 1px solid var(--line); text-align: right; font-size: 1.02rem; }
table.nutri-table tr:last-child td { border-bottom: 0; }
table.nutri-table td.bold-val { font-weight: 700; color: var(--ink); }

.tip-box { margin-top: 1.5rem; padding: 1.1rem 1.2rem; background: #eef6f3; border-right: 5px solid var(--spruce); border-radius: 0 14px 14px 0; line-height: 1.8; font-size: 1rem; box-shadow: 0 2px 6px rgba(31,111,92,0.02); }
.tip-box b { color: var(--spruce-dark); }
.ad-header { color: var(--muted); font-size: .82rem; margin: .8rem 0 .4rem 0; font-weight: 600; letter-spacing: .5px; }
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
            f'<div><div class="cd-title">جاري تحليل ومعالجة صورة الوجبة...</div>'
            f'<div class="cd-sub">سيبدأ فحص السعرات حرارياً خلال {remaining} ثوانٍ تلقائياً</div></div>'
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

    # عرض النتيجة بداخل قالب تصميم فني فاخر وأنيق جداً ومتكامل الألوان
    html_layout = f"""
    <div class="result-card">
        <h2 class="meal-title">{result.meal_name}</h2>
        <div class="meal-subtitle">نتائج تقديرية دقيقة مبنية على المكونات الظاهرة في الصورة</div>
        <div class="kcal-box">
            <span class="kcal-large">{result.calories:.0f}</span>
            <span class="kcal-lbl">سعرة حرارية</span>
        </div>
        <table class="nutri-table">
            <thead>
                <tr>
                    <th>العنصر الغذائي الأساسي</th>
                    <th>الكمية الإجمالية</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="font-weight: 500;">💪 بروتين (Protein)</td>
                    <td class="bold-val" style="color: #3a7fc1;">{result.protein_g:.1f} جم</td>
                </tr>
                <tr>
                    <td style="font-weight: 500;">🥑 دهون صحية وإجمالية (Fats)</td>
                    <td class="bold-val" style="color: #d9695f;">{result.fat_g:.1f} جم</td>
                </tr>
                <tr>
                    <td style="font-weight: 500;">🍞 كربوهيدرات وطاقة (Carbs)</td>
                    <td class="bold-val" style="color: #d8a92f;">{result.carbs_g:.1f} جم</td>
                </tr>
            </tbody>
        </table>
        <div class="tip-box">
            <b>💡 توجيه وإرشاد صحي للوجبة:</b> {result.health_tip}
        </div>
    </div>
    """
    st.markdown(html_layout, unsafe_allow_html=True)
    st.caption("⚠️ التقديرات استرشادية لذكاء صناعي متطور ولا تعني الاستغناء عن أخصائي التغذية الحقيقي.")


# ----------------------------------------------------------------------------
# الواجهة الرسومية المحسنة والجمالية كلياً
# ----------------------------------------------------------------------------
st.markdown(
    '<div class="brand"><div class="brand-mark">🥗</div>'
    '<div class="brand-name">ماسح الوجبات الذكي</div></div>'
    '<div class="tagline">التقط صورة حية لوجبتك الحالية أو ارفعها من معرض الصور، وسيتولى الذكاء الاصطناعي فحص السعرات وعرض المكونات الغذائية فوراً وبشكل منسق.</div>',
    unsafe_allow_html=True
)

# عرض إعلان بنر مرئي مدمج بكود الحساب الخاص بك لضمان الأرباح الفورية
st.markdown('<div class="ad-header">📢 الراعي الرسمي للسيرفر والخادم:</div>', unsafe_allow_html=True)
my_native_ad = """
<script async="async" data-cfasync="false" src="https://profitableratecpmnetwork.com"></script>
<div id="container-0392b334f94fb470d7d8a56c8a5a4f67"></div>
"""
components.html(my_native_ad, height=200)
st.markdown("---")

# تظبيط أزرار الخيارات والتبويبات بشكل شيك ومريح جداً للموبايل
tab_camera, tab_upload = st.tabs(["📷 تشغيل الكاميرا الذكية", "🖼️ استيراد ملف صورة"])

with tab_camera:
    camera_file = st.camera_input("التقط صورة لوجبتك الآن")

with tab_upload:
    uploaded_file = st.file_uploader("اضغط لاختيار ملف وجبتك من المعرض", type=["jpg", "jpeg", "png", "webp"])

image_file = camera_file or uploaded_file

if image_file is not None:
    image_bytes = image_file.getvalue()
    image_hash = hashlib.md5(image_bytes).hexdigest()

    st.image(image_bytes, caption="الصورة المختارة للفحص والتحليل", use_container_width=True)

    if st.session_state.get("last_hash") != image_hash:
        st.session_state["last_hash"] = image_hash
        st.session_state.pop("result", None)
        st.session_state.pop("error", None)

        run_countdown()

        with st.spinner("🤖 جاري تحليل الوجبة وحساب القيم الغذائية بواسطة جيميناي..."):
            try:
                st.session_state["result"] = analyze_meal(image_bytes)
            except Exception as e:
                st.session_state["error"] = str(e)

    if "result" in st.session_state:
        show_result(st.session_state["result"])
    elif "error" in st.session_state:
        st.error("حدث خطأ أثناء الاتصال بالخادم. يرجى التحقق وإعادة المحاولة لاحقاً.")
        st.code(st.session_state["error"])
else:
    st.session_state.pop("last_hash", None)
