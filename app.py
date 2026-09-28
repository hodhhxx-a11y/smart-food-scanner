import hashlib
import html
import io
import time

import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai import types
from PIL import Image
from pydantic import BaseModel

# ----------------------------------------------------------------------------
# الإعدادات العامة
# ----------------------------------------------------------------------------
MODEL_NAME = "gemini-2.5-flash" 
WAIT_SECONDS = 6

st.set_page_config(
    page_title="ماسح الوجبات الذكي",
    page_icon="🥗",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ----------------------------------------------------------------------------
# كود الإعلان (يظهر فقط أثناء مرحلة المعالجة)
# ----------------------------------------------------------------------------
AD_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  html, body { margin: 0; padding: 0; background: transparent; }
  body { display: flex; justify-content: center; align-items: center; min-height: 260px; }
</style>
</head>
<body>
<script async="async" data-cfasync="false" src="https://profitableratecpmnetwork.com"></script>
<div id="container-0392b334f94fb470d7d8a56c8a5a4f67"></div>
</body>
</html>
"""

# ----------------------------------------------------------------------------
# التصميم (CSS)
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

/* الترويسة */
.brand { display: flex; align-items: center; gap: .6rem; margin-bottom: .2rem; }
.brand-mark { width: 38px; height: 38px; border-radius: 11px; background: var(--spruce);
  display: flex; align-items: center; justify-content: center; font-size: 20px; }
.brand-name { font-size: 1.35rem; font-weight: 700; color: var(--ink); }
.tagline { color: var(--muted); margin: .25rem 0 1.4rem; font-size: .98rem; line-height: 1.8; }

/* مؤشر الخطوات */
.steps { display: flex; align-items: center; gap: .5rem; margin: 0 0 1.4rem; }
.step { display: flex; align-items: center; gap: .45rem; color: var(--muted); font-size: .88rem; font-weight: 500; }
.step .dot { width: 24px; height: 24px; border-radius: 50%; border: 1.5px solid var(--line); background: var(--panel);
  display: flex; align-items: center; justify-content: center; font-size: .78rem; font-weight: 600; }
.step.active { color: var(--ink); font-weight: 600; }
.step.active .dot { background: var(--spruce); border-color: var(--spruce); color: #fff; }
.step.done .dot { background: #e3f1ed; border-color: var(--spruce); color: var(--spruce); }
.step-line { flex: 1; height: 1.5px; background: var(--line); min-width: 14px; }

/* التبويبات وعناصر الإدخال */
[data-baseweb="tab-list"] { gap: .4rem; background: #e9efee; padding: 4px; border-radius: 12px; }
[data-baseweb="tab"] { border-radius: 9px; height: 42px; padding: 0 1rem; font-weight: 600; color: var(--muted); }
[data-baseweb="tab"][aria-selected="true"] { background: var(--panel); color: var(--ink); box-shadow: 0 1px 3px rgba(18,38,42,.12); }
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display: none; }
[data-testid="stCameraInput"] video, [data-testid="stCameraInput"] img, [data-testid="stImage"] img {
  border-radius: 16px; }
[data-testid="stFileUploaderDropzone"] { background: var(--panel); border: 1.5px dashed #b6c8c5; border-radius: 16px; padding: 1.6rem; }
[data-testid="stFileUploaderDropzone"]:hover { border-color: var(--spruce); }

/* الأزرار */
.stButton > button { width: 100%; height: 3rem; border-radius: 12px; border: 0; background: var(--spruce);
  color: #fff; font-weight: 600; font-size: 1rem; transition: background .15s; }
.stButton > button:hover { background: var(--spruce-dark); color: #fff; }
.stButton > button:focus-visible { outline: 3px solid #9ed3c6; outline-offset: 2px; }

/* المؤقت */
.cd-wrap { display: flex; align-items: center; gap: 1.1rem; background: var(--panel); border: 1px solid var(--line);
  border-radius: 18px; padding: 1.1rem 1.2rem; margin: 1rem 0; }
.cd-ring { width: 76px; height: 76px; border-radius: 50%; flex: none; display: flex; align-items: center; justify-content: center; }
.cd-inner { width: 58px; height: 58px; border-radius: 50%; background: var(--panel); display: flex; align-items: center;
  justify-content: center; font-size: 1.7rem; font-weight: 700; color: var(--spruce); }
.cd-title { font-weight: 600; font-size: 1.02rem; }
.cd-sub { color: var(--muted); font-size: .9rem; margin-top: .15rem; }
.ad-label { color: var(--muted); font-size: .78rem; margin: .8rem 0 .3rem; }

/* بطاقة النتيجة */
.result { background: var(--panel); border: 1px solid var(--line); border-radius: 20px; padding: 1.4rem 1.4rem 1.2rem; margin-top: 1rem; }
.meal-name { font-size: 1.5rem; font-weight: 700; line-height: 1.5; margin: 0; }
.meal-note { color: var(--muted); font-size: .85rem; margin-top: .1rem; }
.kcal { display: flex; align-items: baseline; gap: .5rem; margin: 1rem 0 .3rem; }
.kcal-num { font-size: 3.2rem; font-weight: 700; color: var(--cal); line-height: 1; }
.kcal-unit { color: var(--muted); font-weight: 500; }
.macro-bar { display: flex; height: 12px; border-radius: 99px; overflow: hidden; background: #edf1f0; margin: .9rem 0 .4rem; }
.macro-bar span { display: block; height: 100%; }
.legend { display: flex; gap: 1rem; flex-wrap: wrap; color: var(--muted); font-size: .82rem; margin-bottom: 1.1rem; }
.legend i { display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-left: .35rem; }

table.nutri { width: 100%; border-collapse: collapse; direction: rtl; }
table.nutri th { text-align: right; color: var(--muted); font-weight: 500; font-size: .82rem; padding: .5rem .3rem; border-bottom: 1px solid var(--line); }
table.nutri td { padding: .8rem .3rem; border-bottom: 1px solid var(--line); text-align: right; font-size: .98rem; }
table.nutri tr:last-child td { border-bottom: 0; }
table.nutri td.val { font-weight: 700; white-space: nowrap; }
.mini { height: 7px; border-radius: 99px; background: #edf1f0; overflow: hidden; min-width: 90px; }
.mini span { display: block; height: 100%; border-radius: 99px; }
.pct { color: var(--muted); font-size: .8rem; margin-top: .2rem; }

.tip { margin-top: 1.1rem; padding: .9rem 1rem; background: #eef6f3; border-right: 4px solid var(--spruce);
  border-radius: 10px; line-height: 1.9; font-size: .97rem; }
.tip b { color: var(--spruce-dark); }
.disclaimer { color: var(--muted); font-size: .8rem; margin: .9rem 0 1.1rem; text-align: center; }

@media (max-width: 480px) {
  .meal-name { font-size: 1.25rem; }
  .kcal-num { font-size: 2.7rem; }
  .step span:last-child { font-size: .8rem; }
}
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

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
- meal_name: اسم الوجبة التقريبي بالعربية (قصير وواضح).
- calories: السعرات الحرارية (kcal).
- protein_g: البروتين بالجرام.
- fat_g: الدهون بالجرام.
- carbs_g: الكربوهيدرات بالجرام.
- health_tip: نصيحة صحية سريعة في جملة أو جملتين بالعربية.
هذه تقديرات تقريبية."""
# ----------------------------------------------------------------------------
# دوال مساعدة
# ----------------------------------------------------------------------------
@st.cache_resource
def get_client() -> genai.Client:
    return genai.Client(api_key="AQ.Ab8RN6JWRZI966GKqBew_h0Vokrt1GPGer_AyzcphzehiUwCYA")


def prepare_image(image_bytes: bytes) -> bytes:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img.thumbnail((1280, 1280))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def analyze_meal(image_bytes: bytes) -> MealAnalysis:
    response = get_client().models.generate_content(
        model=MODEL_NAME,
        contents=[
            {"mime_type": "image/jpeg", "data": prepare_image(image_bytes)},
            PROMPT,
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=MealAnalysis,
            temperature=0.2,
        ),
    )
    return MealAnalysis.model_validate_json(response.text)


def render_header():
    st.markdown(
        '<div class="brand"><div class="brand-mark">🥗</div>'
        '<div class="brand-name">ماسح الوجبات الذكي</div></div>'
        '<div class="tagline">صوّر وجبتك أو ارفع صورتها، وتعرّف على سعراتها ومكوناتها الغذائية خلال ثوانٍ.</div>',
        unsafe_allow_html=True,
    )


def render_steps(active: int):
    labels = ["التقاط الصورة", "المعالجة", "النتيجة"]
    parts = []
    for i, label in enumerate(labels, 1):
        cls = "done" if i < active else ("active" if i == active else "")
        mark = "✓" if i < active else str(i)
        parts.append(f'<div class="step {cls}"><span class="dot">{mark}</span><span>{label}</span></div>')
        if i < len(labels):
            parts.append('<div class="step-line"></div>')
    st.markdown(f'<div class="steps">{"".join(parts)}</div>', unsafe_allow_html=True)


def countdown_html(remaining: int) -> str:
    done = WAIT_SECONDS - remaining + 1
    deg = int(360 * done / WAIT_SECONDS)
    return (
        '<div class="cd-wrap">'
        f'<div class="cd-ring" style="background:conic-gradient(#1f6f5c {deg}deg,#e3ebe9 0deg);">'
        f'<div class="cd-inner">{remaining}</div></div>'
        '<div><div class="cd-title">نجهّز صورتك للتحليل</div>'
        f'<div class="cd-sub">يبدأ التحليل بعد {remaining} ثوانٍ</div></div>'
        '</div>'
    )


def run_countdown():
    timer_box = st.empty()
    ad_label = st.empty()
    ad_box = st.empty()

    ad_label.markdown('<div class="ad-label">إعلان</div>', unsafe_allow_html=True)
    with ad_box.container():
        components.html(AD_HTML, height=280, scrolling=False)

    for remaining in range(WAIT_SECONDS, 0, -1):
        timer_box.markdown(countdown_html(remaining), unsafe_allow_html=True)
        time.sleep(1)

    for box in (timer_box, ad_label, ad_box):
        box.empty()


def result_html(r: MealAnalysis) -> str:
    kcal_p, kcal_c, kcal_f = r.protein_g * 4, r.carbs_g * 4, r.fat_g * 9
    total = kcal_p + kcal_c + kcal_f
    if total > 0:
        pp = round(kcal_p / total * 100)
        cp = round(kcal_c / total * 100)
        fp = max(0, 100 - pp - cp)
    else:
        pp = cp = fp = 0

    name = html.escape(r.meal_name)
    tip = html.escape(r.health_tip)

    def row(label, value, color, pct):
        bar = (
            f'<div class="mini"><span style="width:{pct}%;background:{color};"></span></div>'
            f'<div class="pct">{pct}% من السعرات</div>'
        )
        return f'<tr><td>{label}</td><td class="val">{value}</td><td>{bar}</td></tr>'

    rows = (
        '<tr><td>السعرات الحرارية</td>'
        f'<td class="val">{r.calories:.0f} سعرة</td><td><span class="pct">تقدير للحصة الظاهرة</span></td></tr>'
        + row("البروتين", f"{r.protein_g:.1f} جم", "#3a7fc1", pp)
        + row("الدهون", f"{r.fat_g:.1f} جم", "#d9695f", fp)
        + row("الكربوهيدرات", f"{r.carbs_g:.1f} جم", "#d8a92f", cp)
    )

    return (
        '<div class="result">'
        f'<h2 class="meal-name">{name}</h2>'
        '<div class="meal-note">اسم تقريبي حسب ما ظهر في الصورة</div>'
        f'<div class="kcal"><span class="kcal-num">{r.calories:.0f}</span><span class="kcal-unit">سعرة حرارية</span></div>'
        '<div class="macro-bar">'
        f'<span style="width:{pp}%;background:#3a7fc1;"></span>'
        f'<span style="width:{fp}%;background:#d9695f;"></span>'
        f'<span style="width:{cp}%;background:#d8a92f;"></span>'
        '</div>'
        '<div class="legend">'
        '<span><i style="background:#3a7fc1"></i>بروتين</span>'
        '<span><i style="background:#d9695f"></i>دهون</span>'
        '<span><i style="background:#d8a92f"></i>كربوهيدرات</span>'
        '</div>'
        '<table class="nutri"><thead><tr><th>العنصر</th><th>القيمة</th><th>حصته من السعرات</th></tr></thead>'
        f'<tbody>{rows}</tbody></table>'
        f'<div class="tip"><b>نصيحة صحية:</b> {tip}</div>'
        '</div>'
    )


def reset_app():
    for key in ("stage", "image_bytes", "result", "error"):
        st.session_state.pop(key, None)
    st.session_state["uid"] = st.session_state.get("uid", 0) + 1
    st.rerun()


# ----------------------------------------------------------------------------
# تدفق التطبيق
# ----------------------------------------------------------------------------
stage = st.session_state.get("stage", "input")
uid = st.session_state.get("uid", 0)

render_header()
render_steps({"input": 1, "processing": 2, "ready": 2, "analyzing": 2, "error": 2, "done": 3}.get(stage, 1))

if stage == "input":
    tab_camera, tab_upload = st.tabs(["📷 الكاميرا", "🖼️ من المعرض"])
    with tab_camera:
        camera_file = st.camera_input("التقط صورة واضحة للوجبة", key=f"cam_{uid}")
    with tab_upload:
        uploaded_file = st.file_uploader(
            "اسحب الصورة هنا أو اضغط للاختيار",
            type=["jpg", "jpeg", "png", "webp"],
            key=f"up_{uid}",
        )

    chosen = camera_file or uploaded_file
    if chosen is not None:
        st.session_state["image_bytes"] = chosen.getvalue()
        st.session_state["stage"] = "processing"
        st.rerun()

elif stage == "processing":
    st.image(st.session_state["image_bytes"], use_container_width=True)
    run_countdown()
    st.session_state["stage"] = "ready"
    st.rerun()

elif stage == "ready":
    st.image(st.session_state["image_bytes"], use_container_width=True)
    st.markdown('<div class="ad-label">إعلان</div>', unsafe_allow_html=True)
    components.html(AD_HTML, height=280, scrolling=False)
    st.success("الصورة جاهزة للتحليل.")
    if st.button("ابدأ التحليل"):
        st.session_state["stage"] = "analyzing"
        st.rerun()

elif stage == "analyzing":
    st.image(st.session_state["image_bytes"], use_container_width=True)

    with st.spinner("جارٍ تحليل الوجبة..."):
        try:
            st.session_state["result"] = analyze_meal(st.session_state["image_bytes"])
            st.session_state["stage"] = "done"
        except Exception as exc:  # noqa: BLE001
            st.session_state["error"] = str(exc)
            st.session_state["stage"] = "error"
    st.rerun()

elif stage == "done":
    result: MealAnalysis = st.session_state["result"]
    st.image(st.session_state["image_bytes"], use_container_width=True)

    if not result.is_food:
        st.warning("لم نجد طعامًا في هذه الصورة. جرّب صورة أوضح للوجبة من زاوية أقرب.")
    else:
        st.markdown(result_html(result), unsafe_allow_html=True)
        st.markdown(
            '<div class="disclaimer">القيم تقديرية ولا تغني عن استشارة أخصائي تغذية.</div>',
            unsafe_allow_html=True,
        )

    if st.button("تحليل وجبة جديدة"):
        reset_app()

elif stage == "error":
    st.image(st.session_state["image_bytes"], use_container_width=True)
    st.error("تعذّر تحليل الصورة. تحقق من الاتصال ومن مفتاح Gemini ثم أعد المحاولة.")
    with st.expander("تفاصيل الخطأ"):
        st.code(st.session_state.get("error", ""))

    col1, col2 = st.columns(2)
    with col1:
        if st.button("إعادة المحاولة"):
            st.session_state["stage"] = "analyzing"
            st.rerun()
    with col2:
        if st.button("صورة جديدة"):
            reset_app()
