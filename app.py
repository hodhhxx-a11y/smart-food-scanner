import base64
import html
import io
import os
import time

import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai import types
from PIL import Image, ImageOps
from pydantic import BaseModel

# =============================================================================
# الإعدادات
# =============================================================================
MODEL_NAME = "gemini-3.8-flash" 
"
WAIT_SECONDS = 6

st.set_page_config(
    page_title="ماسح الوجبات الذكي",
    page_icon="🍽️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# كود الإعلان — يظهر أثناء مرحلة المعالجة والتحليل
AD_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  html, body { margin: 0; padding: 0; background: transparent; }
  body { display: flex; justify-content: center; align-items: center; min-height: 250px; }
</style>
</head>
<body>
<script src="https://pl31544285.profitableratecpmnetwork.com/ae/63/60/ae6360bd13a761572e620a61152423ef.js"></script>
</body>
</html>
"""

# =============================================================================
# التصميم
# =============================================================================
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');

:root {
  --navy: #0f2a43;
  --navy-2: #163a5c;
  --amber: #ffb020;
  --ink: #101828;
  --muted: #667085;
  --line: #e4e8ee;
  --bg: #f3f5f9;
  --panel: #ffffff;
}

html, body, [class*="st-"], .stApp, button, input, textarea {
  font-family: 'Tajawal', 'Segoe UI', Tahoma, sans-serif !important;
}
.stApp { background: var(--bg); color: var(--ink); }
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent; height: 0; }
.block-container { direction: rtl; text-align: right; max-width: 700px; padding: 1rem 1rem 3rem; }

/* ---------- الواجهة العلوية ---------- */
.hero { background: linear-gradient(135deg, #0f2a43 0%, #1b4b78 100%); color: #fff; border-radius: 22px;
  padding: 1.7rem 1.5rem 1.6rem; margin-bottom: 1.2rem; position: relative; overflow: hidden; }
.hero::after { content: ""; position: absolute; left: -40px; top: -40px; width: 170px; height: 170px;
  border-radius: 50%; background: rgba(255,176,32,.18); }
.hero-badge { display: inline-block; background: rgba(255,176,32,.2); color: var(--amber); font-weight: 700;
  font-size: .78rem; padding: .25rem .7rem; border-radius: 99px; margin-bottom: .7rem; }
.hero-title { font-size: 1.9rem; font-weight: 800; line-height: 1.35; margin: 0; }
.hero-sub { color: #c9d8e8; margin-top: .5rem; line-height: 1.9; font-size: 1rem; max-width: 30rem; }

/* ---------- الخطوات ---------- */
.steps { display: flex; align-items: center; gap: .5rem; margin: 0 0 1.2rem; }
.step { display: flex; align-items: center; gap: .45rem; color: var(--muted); font-size: .88rem; font-weight: 500; }
.step .dot { width: 26px; height: 26px; border-radius: 50%; border: 1.5px solid var(--line); background: var(--panel);
  display: flex; align-items: center; justify-content: center; font-size: .8rem; font-weight: 700; }
.step.active { color: var(--ink); font-weight: 700; }
.step.active .dot { background: var(--navy); border-color: var(--navy); color: #fff; }
.step.done .dot { background: #fff3d6; border-color: var(--amber); color: #a86a00; }
.step-line { flex: 1; height: 1.5px; background: var(--line); min-width: 12px; }

/* ---------- التبويبات والإدخال ---------- */
[data-baseweb="tab-list"] { gap: .4rem; background: #e6eaf1; padding: 4px; border-radius: 13px; }
[data-baseweb="tab"] { border-radius: 10px; height: 44px; padding: 0 1.1rem; font-weight: 700; color: var(--muted); }
[data-baseweb="tab"][aria-selected="true"] { background: var(--panel); color: var(--navy); box-shadow: 0 1px 4px rgba(16,24,40,.12); }
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display: none; }
[data-testid="stCameraInput"] video, [data-testid="stCameraInput"] img { border-radius: 16px; }
[data-testid="stFileUploaderDropzone"] { background: var(--panel); border: 1.5px dashed #b9c3d3; border-radius: 16px; padding: 1.8rem; }
[data-testid="stFileUploaderDropzone"]:hover { border-color: var(--navy); }

/* ---------- الأزرار ---------- */
.stButton button { width: 100%; height: 3.1rem; border-radius: 13px; border: 0; background: var(--navy);
  color: #fff; font-weight: 700; font-size: 1.02rem; transition: background .15s; }
.stButton button:hover { background: var(--navy-2); color: #fff; }
.stButton button:focus-visible { outline: 3px solid #ffd27a; outline-offset: 2px; }

/* ---------- صورة الوجبة ---------- */
.photo { border-radius: 18px; overflow: hidden; background: #dfe5ee; margin-bottom: 1rem; }
.photo img { display: block; width: 100%; max-height: 380px; object-fit: cover; }

/* ---------- العدّاد ---------- */
.cd-wrap { display: flex; align-items: center; gap: 1.1rem; background: var(--panel); border: 1px solid var(--line);
  border-radius: 18px; padding: 1.1rem 1.2rem; margin: 0 0 .9rem; }
.cd-ring { width: 74px; height: 74px; border-radius: 50%; flex: none; display: flex; align-items: center; justify-content: center; }
.cd-inner { width: 56px; height: 56px; border-radius: 50%; background: var(--panel); display: flex; align-items: center;
  justify-content: center; font-size: 1.7rem; font-weight: 800; color: var(--navy); }
.cd-title { font-weight: 700; font-size: 1.05rem; }
.cd-sub { color: var(--muted); font-size: .9rem; margin-top: .15rem; }
.ad-label { color: var(--muted); font-size: .78rem; margin: .4rem 0 .3rem; }

/* ---------- بطاقة النتيجة ---------- */
.card { background: var(--panel); border: 1px solid var(--line); border-radius: 20px; padding: 1.4rem; margin-bottom: 1rem; }
.head { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; }
.meal-name { font-size: 1.6rem; font-weight: 800; line-height: 1.4; margin: 0; }
.portion { color: var(--muted); font-size: .92rem; margin-top: .2rem; }
.score { flex: none; text-align: center; border-radius: 14px; padding: .55rem .8rem; min-width: 84px; }
.score b { display: block; font-size: 1.6rem; line-height: 1.1; font-weight: 800; }
.score span { font-size: .74rem; font-weight: 700; }
.score.good { background: #e6f6ee; color: #14804a; }
.score.mid { background: #fff3d6; color: #a86a00; }
.score.low { background: #fde8ea; color: #b42335; }

.overview { display: flex; align-items: center; gap: 1.6rem; margin: 1.3rem 0 .4rem; }
.donut { width: 158px; height: 158px; border-radius: 50%; flex: none; display: flex; align-items: center; justify-content: center; }
.donut-in { width: 112px; height: 112px; border-radius: 50%; background: var(--panel); display: flex; flex-direction: column;
  align-items: center; justify-content: center; }
.donut-num { font-size: 2.1rem; font-weight: 800; color: var(--navy); line-height: 1; }
.donut-lbl { color: var(--muted); font-size: .78rem; margin-top: .2rem; }
.legend { flex: 1; display: flex; flex-direction: column; gap: .7rem; }
.lg { display: flex; align-items: center; justify-content: space-between; font-size: .98rem; }
.lg i { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-left: .5rem; }
.lg b { font-weight: 800; }
.lg small { color: var(--muted); font-weight: 500; margin-right: .4rem; }

.sec-title { font-weight: 800; font-size: 1.05rem; margin: 0 0 .5rem; }
table.nt { width: 100%; border-collapse: collapse; direction: rtl; }
table.nt th { text-align: right; color: var(--muted); font-weight: 500; font-size: .8rem; padding: .5rem .3rem; border-bottom: 1px solid var(--line); }
table.nt td { padding: .75rem .3rem; border-bottom: 1px solid var(--line); text-align: right; font-size: .98rem; vertical-align: middle; }
table.nt tr:last-child td { border-bottom: 0; }
table.nt td.v { font-weight: 800; white-space: nowrap; }
.bar { height: 7px; border-radius: 99px; background: #edf0f5; overflow: hidden; min-width: 80px; }
.bar span { display: block; height: 100%; border-radius: 99px; }
.pct { color: var(--muted); font-size: .78rem; margin-top: .2rem; }

.chips { display: flex; flex-wrap: wrap; gap: .5rem; }
.chip { background: #eef2f8; color: var(--navy); border-radius: 99px; padding: .3rem .85rem; font-size: .9rem; font-weight: 500; }

.tip { background: #fff8e6; border-right: 4px solid var(--amber); border-radius: 12px; padding: 1rem 1.1rem; line-height: 1.95; font-size: 1rem; }
.tip b { color: #8a5600; }
.note { color: var(--muted); font-size: .8rem; text-align: center; margin: .6rem 0 1.1rem; line-height: 1.8; }

@media (max-width: 520px) {
  .hero-title { font-size: 1.5rem; }
  .meal-name { font-size: 1.3rem; }
  .overview { flex-direction: column; align-items: stretch; gap: 1.1rem; }
  .donut { align-self: center; }
  .step span:last-child { font-size: .78rem; }
}
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# =============================================================================
# نموذج البيانات المطلوب من Gemini
# =============================================================================
class MealAnalysis(BaseModel):
    is_food: bool
    meal_name: str
    portion: str
    calories: float
    protein_g: float
    fat_g: float
    carbs_g: float
    fiber_g: float
    sugar_g: float
    health_score: int
    ingredients: list[str]
    health_tip: str


PROMPT = """أنت خبير تغذية. حلل صورة الوجبة المرفقة وقدّر القيم الغذائية للحصة الظاهرة في الصورة فقط.
- is_food: false إذا لم يظهر طعام في الصورة، وعندها ضع 0 في كل القيم الرقمية وقائمة فارغة للمكونات.
- meal_name: اسم الوجبة التقريبي بالعربية (قصير وواضح).
- portion: وصف مختصر للحصة الظاهرة (مثال: طبق متوسط، حوالي 350 جم).
- calories: السعرات الحرارية (kcal).
- protein_g / fat_g / carbs_g / fiber_g / sugar_g: القيم بالجرام.
- health_score: تقييم صحي للوجبة من 1 إلى 10.
- ingredients: أهم المكونات الظاهرة (من 3 إلى 8 عناصر) بالعربية.
- health_tip: نصيحة صحية سريعة عملية في جملة أو جملتين بالعربية.
هذه تقديرات تقريبية."""


# =============================================================================
# دوال مساعدة
# =============================================================================
def load_api_key() -> str:
    """يقرأ المفتاح من Streamlit Secrets، أو من متغير بيئة GEMINI_API_KEY."""
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        return os.environ.get("GEMINI_API_KEY", "")


@st.cache_resource
def get_client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)


def prepare_image(raw: bytes) -> bytes:
    """يعدّل اتجاه الصورة ويصغّرها ويحوّلها إلى JPEG."""
    img = Image.open(io.BytesIO(raw))
    img = ImageOps.exif_transpose(img).convert("RGB")
    img.thumbnail((1280, 1280))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def analyze_meal(image_bytes: bytes) -> MealAnalysis:
    client = get_client(load_api_key())
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
            PROMPT,
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=MealAnalysis,
            temperature=0.2,
        ),
    )
    return MealAnalysis.model_validate_json(response.text)


def photo_html(image_bytes: bytes) -> str:
    b64 = base64.b64encode(image_bytes).decode("ascii")
    return f'<div class="photo"><img src="data:image/jpeg;base64,{b64}" alt="صورة الوجبة"></div>'


def render_header():
    st.markdown(
        '<div class="hero">'
        '<div class="hero-badge">مدعوم بالذكاء الاصطناعي</div>'
        '<div class="hero-title">ماسح الوجبات الذكي</div>'
        '<div class="hero-sub">صوّر وجبتك أو ارفع صورتها، واعرف سعراتها والبروتين والدهون '
        'والكربوهيدرات خلال ثوانٍ.</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def render_steps(active: int):
    labels = ["التقاط الصورة", "المعالجة والتحليل", "النتيجة"]
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
        f'<div class="cd-ring" style="background:conic-gradient(#ffb020 {deg}deg,#e4e8ee 0deg);">'
        f'<div class="cd-inner">{remaining}</div></div>'
        '<div><div class="cd-title">نجهّز صورتك للتحليل</div>'
        f'<div class="cd-sub">يبدأ التحليل بعد {remaining} ثوانٍ</div></div>'
        '</div>'
    )


def analyzing_html() -> str:
    return (
        '<div class="cd-wrap">'
        '<div class="cd-ring" style="background:conic-gradient(#ffb020 360deg,#e4e8ee 0deg);">'
        '<div class="cd-inner">🤖</div></div>'
        '<div><div class="cd-title">جارٍ تحليل الوجبة</div>'
        '<div class="cd-sub">لحظات ويظهر لك التقرير الغذائي</div></div>'
        '</div>'
    )


def result_html(r: MealAnalysis, image_bytes: bytes) -> str:
    cal = max(0.0, r.calories)
    protein = max(0.0, r.protein_g)
    fat = max(0.0, r.fat_g)
    carbs = max(0.0, r.carbs_g)
    fiber = max(0.0, r.fiber_g)
    sugar = max(0.0, r.sugar_g)
    score = min(10, max(1, int(r.health_score)))

    # توزيع السعرات على العناصر الثلاثة
    kp, kc, kf = protein * 4, carbs * 4, fat * 9
    total = kp + kc + kf
    if total > 0:
        pp = round(kp / total * 100)
        cp = round(kc / total * 100)
        fp = max(0, 100 - pp - cp)
        donut_bg = (
            f"conic-gradient(#2f7be0 0% {pp}%, #f0a81f {pp}% {pp + cp}%, #e5566d {pp + cp}% 100%)"
        )
    else:
        pp = cp = fp = 0
        donut_bg = "conic-gradient(#e4e8ee 0% 100%)"

    if score >= 7:
        score_cls, score_txt = "good", "وجبة ممتازة"
    elif score >= 4:
        score_cls, score_txt = "mid", "وجبة متوسطة"
    else:
        score_cls, score_txt = "low", "تحتاج تحسين"

    def dv_row(label, value_txt, val, ref, color):
        pct = round(val / ref * 100) if ref else 0
        width = min(100, pct)
        return (
            f'<tr><td>{label}</td><td class="v">{value_txt}</td>'
            f'<td><div class="bar"><span style="width:{width}%;background:{color};"></span></div>'
            f'<div class="pct">{pct}% من الاحتياج اليومي</div></td></tr>'
        )

    rows = (
        dv_row("السعرات الحرارية", f"{cal:.0f} سعرة", cal, 2000, "#e8801f")
        + dv_row("البروتين", f"{protein:.1f} جم", protein, 50, "#2f7be0")
        + dv_row("الدهون", f"{fat:.1f} جم", fat, 78, "#e5566d")
        + dv_row("الكربوهيدرات", f"{carbs:.1f} جم", carbs, 275, "#f0a81f")
        + dv_row("الألياف", f"{fiber:.1f} جم", fiber, 28, "#2fa66a")
        + dv_row("السكريات", f"{sugar:.1f} جم", sugar, 50, "#9b6bd6")
    )

    chips = "".join(f'<span class="chip">{html.escape(str(i))}</span>' for i in r.ingredients[:10])
    ingredients_block = (
        f'<div class="card"><div class="sec-title">أهم المكونات الظاهرة</div><div class="chips">{chips}</div></div>'
        if chips
        else ""
    )

    return (
        photo_html(image_bytes)
        + '<div class="card">'
        '<div class="head"><div>'
        f'<div class="meal-name">{html.escape(r.meal_name)}</div>'
        f'<div class="portion">{html.escape(r.portion)}</div></div>'
        f'<div class="score {score_cls}"><b>{score}/10</b><span>{score_txt}</span></div></div>'
        '<div class="overview">'
        f'<div class="donut" style="background:{donut_bg};"><div class="donut-in">'
        f'<div class="donut-num">{cal:.0f}</div><div class="donut-lbl">سعرة حرارية</div></div></div>'
        '<div class="legend">'
        f'<div class="lg"><span><i style="background:#2f7be0"></i>البروتين</span><span><b>{protein:.1f} جم</b><small>{pp}%</small></span></div>'
        f'<div class="lg"><span><i style="background:#e5566d"></i>الدهون</span><span><b>{fat:.1f} جم</b><small>{fp}%</small></span></div>'
        f'<div class="lg"><span><i style="background:#f0a81f"></i>الكربوهيدرات</span><span><b>{carbs:.1f} جم</b><small>{cp}%</small></span></div>'
        '</div></div></div>'
        '<div class="card"><div class="sec-title">القيم الغذائية</div>'
        '<table class="nt"><thead><tr><th>العنصر</th><th>الكمية</th><th>من الاحتياج اليومي</th></tr></thead>'
        f'<tbody>{rows}</tbody></table></div>'
        + ingredients_block
        + f'<div class="tip"><b>💡 نصيحة صحية:</b> {html.escape(r.health_tip)}</div>'
        '<div class="note">القيم تقديرية (نسبة الاحتياج اليومي محسوبة على نظام 2000 سعرة) '
        'ولا تغني عن استشارة أخصائي تغذية.</div>'
    )


def reset_app():
    for key in ("stage", "image_bytes", "result", "error", "skip_wait"):
        st.session_state.pop(key, None)
    st.session_state["uid"] = st.session_state.get("uid", 0) + 1
    st.rerun()


# =============================================================================
# تدفق التطبيق
# =============================================================================
render_header()

if not load_api_key():
    st.error("مفتاح Gemini غير مضبوط. أضف GEMINI_API_KEY في ملف .streamlit/secrets.toml ثم أعد تشغيل التطبيق.")
    st.stop()

stage = st.session_state.get("stage", "input")
uid = st.session_state.get("uid", 0)

render_steps({"input": 1, "processing": 2, "error": 2, "done": 3}.get(stage, 1))

# ---------- 1) اختيار الصورة ----------
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
        try:
            st.session_state["image_bytes"] = prepare_image(chosen.getvalue())
            st.session_state["stage"] = "processing"
            st.rerun()
        except Exception:
            st.error("تعذّر قراءة الصورة. جرّب صورة أخرى بصيغة JPG أو PNG.")

# ---------- 2) الانتظار + التحليل ----------
elif stage == "processing":
    image_bytes = st.session_state["image_bytes"]
    st.markdown(photo_html(image_bytes), unsafe_allow_html=True)

    timer_box = st.empty()
    label_box = st.empty()
    ad_box = st.empty()

    label_box.markdown('<div class="ad-label">إعلان</div>', unsafe_allow_html=True)
    with ad_box.container():
        components.html(AD_HTML, height=270, scrolling=False)

    if not st.session_state.pop("skip_wait", False):
        for remaining in range(WAIT_SECONDS, 0, -1):
            timer_box.markdown(countdown_html(remaining), unsafe_allow_html=True)
            time.sleep(1)

    timer_box.markdown(analyzing_html(), unsafe_allow_html=True)
    try:
        st.session_state["result"] = analyze_meal(image_bytes)
        st.session_state["stage"] = "done"
    except Exception as exc:  # noqa: BLE001
        st.session_state["error"] = str(exc)
        st.session_state["stage"] = "error"
    st.rerun()

# ---------- 3) النتيجة ----------
elif stage == "done":
    result: MealAnalysis = st.session_state["result"]
    image_bytes = st.session_state["image_bytes"]

    if not result.is_food:
        st.markdown(photo_html(image_bytes), unsafe_allow_html=True)
        st.warning("لم نجد طعامًا في هذه الصورة. جرّب صورة أوضح للوجبة من زاوية أقرب.")
    else:
        st.markdown(result_html(result, image_bytes), unsafe_allow_html=True)

    if st.button("تحليل وجبة جديدة"):
        reset_app()

# ---------- خطأ ----------
elif stage == "error":
    st.markdown(photo_html(st.session_state["image_bytes"]), unsafe_allow_html=True)
    st.error("تعذّر تحليل الصورة. تحقق من الاتصال ومن مفتاح Gemini ثم أعد المحاولة.")
    with st.expander("تفاصيل الخطأ"):
        st.code(st.session_state.get("error", ""))

    col1, col2 = st.columns(2)
    with col1:
        if st.button("إعادة المحاولة"):
            st.session_state["skip_wait"] = True
            st.session_state["stage"] = "processing"
            st.rerun()
    with col2:
        if st.button("صورة جديدة"):
            reset_app()
