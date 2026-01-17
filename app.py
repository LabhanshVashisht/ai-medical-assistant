import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os
from pypdf import PdfReader
import matplotlib.pyplot as plt

# ---------- LOAD ENV ----------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="AI Medical Assistant",
    page_icon="🩺",
    layout="wide"
)

# ---------- HERO HEADER ----------
st.markdown("""
<div style="padding:24px;border-radius:14px;
background:linear-gradient(90deg,#2E86AB,#1B4F72);
color:white">
<h1>🩺 AI Medical Assistant</h1>
<p>Expert medical guidance • Health analytics • Privacy-first</p>
</div>
""", unsafe_allow_html=True)

# ---------- SYSTEM PROMPTS ----------
SYSTEM_PROMPT = """
You are an expert medical assistant.
You provide accurate, evidence-based medical information.
You DO NOT diagnose diseases or prescribe medicines.

Include:
1. Possible causes
2. General self-care advice
3. When to see a doctor
4. Emergency warning signs

Use simple language.
End with a medical disclaimer.
"""

PDF_PROMPT = """
You are a medical expert.
Explain the following medical report in simple language.
Mention:
- Test names
- Normal vs abnormal values
- Possible meaning
- When to consult a doctor

Do not diagnose or prescribe.
End with a disclaimer.
"""

# ---------- SESSION STATE ----------
if "severity_trend" not in st.session_state:
    st.session_state.severity_trend = []

# ---------- SYMPTOM EXTRACTION ----------
def extract_symptoms(text):
    keywords = [
        "fever", "cough", "pain", "headache", "fatigue",
        "vomiting", "nausea", "dizziness", "breath",
        "infection", "diarrhea", "cold"
    ]
    text = text.lower()
    return [k for k in keywords if k in text]

# ---------- SIDEBAR ----------
st.sidebar.markdown("## 🧭 Navigation")
page = st.sidebar.radio(
    "Choose a section",
    ["Medical Assistant", "Health Dashboard", "Medical Report Explainer"]
)

st.sidebar.markdown("---")
st.sidebar.info("⚠️ Educational use only")

# ===============================
# MEDICAL ASSISTANT
# ===============================
if page == "Medical Assistant":

    st.subheader("🧠 Describe Your Symptoms")

    user_input = st.text_area(
        "",
        placeholder="Example: I have fever and headache for two days...",
        height=130
    )

    if st.button("Get Medical Advice"):
        if user_input.strip():
            with st.spinner("Analyzing symptoms..."):
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_input}
                    ],
                    temperature=0.3
                )
                answer = response.choices[0].message.content

            with st.container(border=True):
                st.subheader("🩺 Medical Insight")
                st.write(answer)

            # ---- analytics ----
            symptoms = extract_symptoms(user_input)
            st.session_state.severity_trend.append(len(symptoms))
        else:
            st.warning("Please enter your symptoms.")

# ===============================
# HEALTH DASHBOARD
# ===============================
elif page == "Health Dashboard":

    st.subheader("📈 Health Analysis Dashboard")

    if not st.session_state.severity_trend:
        st.info("No health data yet. Ask medical questions first.")
        st.stop()

    visits = list(range(1, len(st.session_state.severity_trend) + 1))
    severity = st.session_state.severity_trend

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Consultations", len(visits))
    col2.metric("Latest Severity", severity[-1])
    col3.metric("Health Status", "Stable" if severity[-1] <= 2 else "Needs Attention")

    st.markdown("### Symptom Severity Over Time")

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(visits, severity, marker="o", linewidth=2)
    ax.set_xlabel("Consultation Number")
    ax.set_ylabel("Number of Symptoms")
    ax.grid(alpha=0.3)
    st.pyplot(fig)

    st.markdown("### Cumulative Health Load")

    cumulative = []
    total = 0
    for s in severity:
        total += s
        cumulative.append(total)

    fig2, ax2 = plt.subplots(figsize=(6, 4))
    ax2.plot(visits, cumulative, marker="o", linewidth=2)
    ax2.set_xlabel("Consultation Number")
    ax2.set_ylabel("Cumulative Symptom Score")
    ax2.grid(alpha=0.3)
    st.pyplot(fig2)

# ===============================
# MEDICAL REPORT EXPLAINER
# ===============================
elif page == "Medical Report Explainer":

    st.subheader("📄 Medical Report Explanation")

    uploaded_file = st.file_uploader(
        "Upload a medical report (PDF)",
        type="pdf"
    )

    if uploaded_file:
        reader = PdfReader(uploaded_file)
        extracted_text = ""

        for p in reader.pages:
            extracted_text += p.extract_text() + "\n"

        if st.button("Explain Report"):
            with st.spinner("Analyzing report..."):
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": PDF_PROMPT},
                        {"role": "user", "content": extracted_text[:12000]}
                    ],
                    temperature=0.2
                )
                explanation = response.choices[0].message.content

            with st.container(border=True):
                st.subheader("🧾 Report Explanation")
                st.write(explanation)

# ---------- FOOTER ----------
st.markdown("---")
st.caption(
    "⚠️ This application is for educational purposes only and does not replace professional medical advice."
)
