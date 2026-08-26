import base64, json, os, re
from pathlib import Path
import streamlit as st

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

try:
    import fitz
except Exception:
    fitz = None

st.set_page_config(page_title="AI Engineering Drawing & Manufacturing Risk Checker", page_icon="⚙️", layout="wide")

DEMO_RESULT = {
    "part_name": "Stepped Shaft", "part_number": "SH-250-01", "revision": "02",
    "material": "EN8",
    "dimensions": ["Overall length: 250 mm", "Main diameter: Ø50 ±0.02 mm", "Step diameter: Ø40 mm", "Keyway: 12 × 8 mm"],
    "features": ["Stepped cylindrical geometry", "Keyway", "M20 thread"],
    "threads": ["M20 — pitch / thread standard should be confirmed"],
    "tolerances": ["Ø50 ±0.02 mm", "General tolerance ±0.10 mm unless otherwise specified"],
    "surface_finishes": ["Ra 0.8 µm (critical journal)"],
    "risks": [
        {"level":"HIGH","issue":"Tight dimensional tolerance: Ø50 ±0.02 mm",
         "recommendation":"Verify machine/process capability and the selected finishing method before production. Inspect using suitable calibrated equipment."},
        {"level":"MEDIUM","issue":"Critical surface finish: Ra 0.8 µm",
         "recommendation":"Confirm the finishing operation and define an appropriate surface-roughness inspection method."},
        {"level":"LOW","issue":"M20 thread is specified but pitch / thread standard is not explicit",
         "recommendation":"Confirm the thread pitch/standard before manufacture and inspect with an appropriate calibrated thread gauge."}
    ],
    "manufacturing_process": ["Raw material preparation","CNC turning","Keyway milling","Threading","Finishing","Final inspection"],
    "inspection_checklist": ["Verify Ø50 ±0.02 mm","Verify Ø40 mm","Verify overall 250 mm length","Verify keyway 12 × 8 mm","Confirm M20 pitch / thread standard","Inspect M20 thread with suitable gauge","Verify Ra 0.8 µm","Verify drawing revision before release"],
    "clarifications": ["Confirm M20 thread pitch / thread standard.","Confirm the manufacturing route can achieve the ±0.02 mm requirement.","Confirm the specified surface finish inspection method."]
}

SYSTEM_PROMPT = """
You are an AI engineering drawing analysis assistant for a hackathon prototype.
Analyze the uploaded engineering drawing image.

Extract only information visible or strongly supported by the drawing. Never invent a dimension or material.
If information is unclear, put it in clarifications.
Risk analysis is a screening aid, not a manufacturing release decision.
Return ONLY valid JSON with these keys:
part_name, part_number, revision, material, dimensions, features, threads, tolerances,
surface_finishes, risks, manufacturing_process, inspection_checklist, clarifications.
risks must contain objects with level (HIGH/MEDIUM/LOW), issue, recommendation.

Flag tight tolerances for process-capability review, fine surface finishes for finishing/inspection review,
threads for pitch/standard confirmation when not explicit, and missing critical information.
Do not claim a process is guaranteed to achieve a tolerance.
"""

def pdf_to_png(data):
    if fitz is None:
        raise RuntimeError("PDF support needs PyMuPDF. Run pip install -r requirements.txt")
    doc = fitz.open(stream=data, filetype="pdf")
    if not len(doc):
        raise RuntimeError("PDF contains no pages.")
    pix = doc[0].get_pixmap(matrix=fitz.Matrix(2,2), alpha=False)
    return pix.tobytes("png")

def image_bytes(uploaded):
    data = uploaded.getvalue()
    return pdf_to_png(data) if uploaded.name.lower().endswith(".pdf") else data

def ai_analyze(data, model):
    if OpenAI is None:
        raise RuntimeError("OpenAI SDK missing. Install requirements.txt")
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set.")
    client = OpenAI(api_key=key)
    url = "data:image/png;base64," + base64.b64encode(data).decode()
    response = client.responses.create(
        model=model,
        instructions=SYSTEM_PROMPT,
        input=[{"role":"user","content":[
            {"type":"input_text","text":"Analyze this engineering drawing and return JSON only."},
            {"type":"input_image","image_url":url,"detail":"high"}
        ]}],
        text={"format":{"type":"json_object"}},
        max_output_tokens=2500
    )
    raw = response.output_text
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.S)
        if not m: raise RuntimeError("AI returned non-JSON output.")
        return json.loads(m.group(0))

def render_risk(r):
    level = str(r.get("level","LOW")).upper()
    cfg = {"HIGH":("🔴","#FDECEC","#B91C1C"),"MEDIUM":("🟡","#FFF7E6","#B45309"),"LOW":("🟢","#ECFDF5","#047857")}
    icon,bg,fg = cfg.get(level,("⚪","#F3F4F6","#374151"))
    st.markdown(f"""<div style="padding:16px;border-radius:12px;background:{bg};border-left:6px solid {fg};margin:10px 0">
    <b style="color:{fg}">{icon} {level} RISK</b><br><b>{r.get("issue","")}</b><br>
    <small><b>Recommendation:</b> {r.get("recommendation","")}</small></div>""", unsafe_allow_html=True)

st.markdown("""<style>
.main-title{font-size:34px;font-weight:800;color:#0F1F34}.sub{color:#667085}
.section{font-size:21px;font-weight:750;color:#0F1F34;margin-top:20px}
</style>""", unsafe_allow_html=True)
st.markdown('<div class="main-title">⚙️ AI Engineering Drawing & Manufacturing Risk Checker</div>', unsafe_allow_html=True)
st.markdown('<div class="sub">AI-assisted drawing interpretation • manufacturing risk screening • inspection checklist</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("Analysis Mode")
    mode = st.radio("Choose mode", ["Demo Mode","AI Mode"])
    model = st.text_input("AI model", value=os.getenv("OPENAI_MODEL","gpt-5.6-luna"))
    st.caption("AI Mode requires OPENAI_API_KEY.")
    st.divider()
    st.caption("For the hackathon video, use Demo Mode unless AI Mode has been tested repeatedly.")

uploaded = st.file_uploader("Upload an engineering drawing", type=["png","jpg","jpeg","pdf"])
c1,c2 = st.columns(2)
with c1: analyze = st.button("🔍 ANALYZE DRAWING", type="primary", use_container_width=True)
with c2: load_demo = st.button("📐 LOAD DEMO DRAWING", use_container_width=True)

if load_demo:
    p = Path(__file__).parent/"sample_drawings"/"Step2_Sample_Stepped_Shaft_Engineering_Drawing.png"
    if p.exists():
        st.session_state["image"] = p.read_bytes()
        st.session_state["name"] = p.name
    else:
        st.error("Demo drawing not found.")

if uploaded:
    st.session_state["image"] = image_bytes(uploaded)
    st.session_state["name"] = uploaded.name

data = st.session_state.get("image")
name = st.session_state.get("name")

if data:
    st.markdown('<div class="section">Drawing Preview</div>', unsafe_allow_html=True)
    st.image(data, caption=name, use_container_width=True)

if analyze or load_demo:
    if not data:
        st.warning("Upload or load a drawing first.")
        st.stop()
    if mode == "Demo Mode":
        st.session_state["result"] = DEMO_RESULT
        st.success("Demo analysis completed.")
    else:
        with st.spinner("AI is analyzing the drawing..."):
            try:
                st.session_state["result"] = ai_analyze(data, model)
                st.success("AI analysis completed.")
            except Exception as e:
                st.error(str(e))
                st.info("Switch to Demo Mode for the guaranteed hackathon demonstration.")

result = st.session_state.get("result")
if result:
    st.divider()
    st.markdown('<div class="section">1. Drawing Information</div>', unsafe_allow_html=True)
    a,b,c,d = st.columns(4)
    a.metric("Part", result.get("part_name") or "Not detected")
    b.metric("Material", result.get("material") or "Not detected")
    c.metric("Revision", result.get("revision") or "Not detected")
    d.metric("Part No.", result.get("part_number") or "Not detected")

    left,right = st.columns(2)
    with left:
        st.subheader("Dimensions")
        for x in result.get("dimensions",[]): st.write("•",x)
        st.subheader("Features")
        for x in result.get("features",[]): st.write("•",x)
        st.subheader("Threads")
        for x in result.get("threads",[]): st.write("•",x)
    with right:
        st.subheader("Tolerances")
        for x in result.get("tolerances",[]): st.write("•",x)
        st.subheader("Surface Finish")
        for x in result.get("surface_finishes",[]): st.write("•",x)

    st.markdown('<div class="section">2. Manufacturing Risk Analysis</div>', unsafe_allow_html=True)
    for r in result.get("risks",[]): render_risk(r)

    st.markdown('<div class="section">3. Recommended Manufacturing Sequence</div>', unsafe_allow_html=True)
    process = result.get("manufacturing_process",[])
    if process:
        cols=st.columns(min(4,len(process)))
        for i,step in enumerate(process): cols[i%len(cols)].markdown(f"**{i+1}.** {step}")

    st.markdown('<div class="section">4. Inspection Checklist</div>', unsafe_allow_html=True)
    for i,item in enumerate(result.get("inspection_checklist",[])):
        st.checkbox(str(item), key=f"inspection_{i}_{abs(hash(str(item)))}")

    st.markdown('<div class="section">5. Engineer Clarifications</div>', unsafe_allow_html=True)
    for x in result.get("clarifications",[]): st.warning(x)

    st.download_button("⬇️ Export Analysis JSON", json.dumps(result,indent=2,ensure_ascii=False),
                       "engineering_drawing_analysis.json","application/json")

st.divider()
st.caption("Prototype disclaimer: AI is decision support. Final drawing approval, process validation and inspection planning remain with a qualified engineer.")
