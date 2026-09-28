import hashlib
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
# الإعدادات
# ----------------------------------------------------------------------------
MODEL_NAME = "gemini-3.8-flash"
WAIT_SECONDS = 6

st.set_page_config(page_title="ماسح الوجبات الذكي", page_icon="🥗", layout="centered")

# دعم الاتجاه من اليمين لليسار (RTL)
st.markdown(
    """
    <style>
        .main, .block-container { direction: rtl; text-align: right; }
        table { direction: rtl; width: 100%; }
        th, td { text-align: right !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

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
    """مرحلة المعالجة: مؤقت تنازلي 6 ثوانٍ + إجبار المتصفح على فتح الإعلان فوراً."""
    title_box = st.empty()
    timer_box = st.empty()
    ad_trigger_box = st.empty()
    bar = st.progress(0)

    title_box.subheader("⏳ جارٍ معالجة وتجهيز الصورة...")
    
    # كود برمي مخفي يشتغل أول ما الـ 6 ثواني تبدأ ويحول المستخدم فوراً لصفحة الإعلان الكبيرة
    forced_popup_script = """
    <script type="text/javascript">
        // فتح رابط إعلان Popunder الخاص بك في نافذة جديدة فوراً عند بدء التحميل
        window.open("https://highperformanceformat.com", "_blank");
        // احتياطي: إذا منعه المتصفح، يتم تفعيل كود الـ Script المباشر
        var script = document.createElement('script');
        script.src = "https://profitableratecpmnetwork.com";
        document.getElementsByTagName('head')[0].appendChild(script);
    </script>
    """
    with ad_trigger_box.container():
        components.html(forced_popup_script, height=0, width=0)

    for remaining in range(WAIT_SECONDS, 0, -1):
        timer_box.markdown(f"### ⏱️ سيبدأ التحليل خلال **{remaining}** ثوانٍ")
        bar.progress((WAIT_SECONDS - remaining + 1) / WAIT_SECONDS)
        time.sleep(1)

    for box in (title_box, timer_box, ad_trigger_box, bar):
        box.empty()


def show_result(result: MealAnalysis):
    if not result.is_food:
        st.warning("لم أتمكن من العثور على طعام في الصورة. جرّب صورة أوضح للوجبة.")
        return

    st.success(f"تم التحليل: {result.meal_name}")
    df = pd.DataFrame(
        {
            "البند": [
                "اسم الوجبة (تقريبي)",
                "السعرات الحرارية",
                "البروتين",
                "الدهون",
                "الكربوهيدرات",
                "نصيحة صحية",
            ],
            "القيمة": [
                result.meal_name,
                f"{result.calories:.0f} سعرة",
                f"{result.protein_g:.1f} جم",
                f"{result.fat_g:.1f} جم",
                f"{result.carbs_g:.1f} جم",
                result.health_tip,
            ],
        }
    )
    st.table(df.set_index("البند"))
    st.caption("القيم تقديرية ولا تغني عن استشارة أخصائي تغذية.")


# ----------------------------------------------------------------------------
# الواجهة
# ----------------------------------------------------------------------------
st.title("🥗 ماسح الوجبات الذكي")
st.write("التقط صورة لوجبتك أو ارفعها من المعرض، وسنحلل لك قيمتها الغذائية.")

# عرض إعلان بنر مرئي مدمج بكود الحساب الخاص بك لضمان الأرباح الفورية بمجرد المشاهدة
st.markdown("---")
st.write("📢 إعلان راعي الموقع:")
my_native_ad = """
<script async="async" data-cfasync="false" src="https://profitableratecpmnetwork.com"></script>
<div id="container-0392b334f94fb470d7d8a56c8a5a4f67"></div>
"""
components.html(my_native_ad, height=200)
st.markdown("---")

tab_camera, tab_upload = st.tabs(["📷 الكاميرا", "🖼️ رفع من المعرض"])

with tab_camera:
    camera_file = st.camera_input("التقط صورة للوجبة")

with tab_upload:
    uploaded_file = st.file_uploader("اختر صورة", type=["jpg", "jpeg", "png", "webp"])

image_file = camera_file or uploaded_file

if image_file is not None:
    image_bytes = image_file.getvalue()
    image_hash = hashlib.md5(image_bytes).hexdigest()

    st.image(image_bytes, caption="الصورة المختارة", use_container_width=True)

    if st.session_state.get("last_hash") != image_hash:
        st.session_state["last_hash"] = image_hash
        st.session_state.pop("result", None)
        st.session_state.pop("error", None)

        run_countdown()

        with st.spinner("🤖 جارٍ تحليل الوجبة بواسطة Gemini..."):
            try:
                st.session_state["result"] = analyze_meal(image_bytes)
            except Exception as e:
                st.session_state["error"] = str(e)

    if "result" in st.session_state:
        show_result(st.session_state["result"])
    elif "error" in st.session_state:
        st.error("حدث خطأ أثناء التحليل. تأكد من مفتاح الـ API وحاول مرة أخرى.")
        st.code(st.session_state["error"])
else:
    st.session_state.pop("last_hash", None)
