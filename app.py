import streamlit as st
from dotenv import load_dotenv
import os
from PIL import Image
from pypdf import PdfReader
import matplotlib.pyplot as plt

from prompts.system_prompt import SYSTEM_PROMPT
from prompts.pdf_prompt import PDF_PROMPT
from prompts.pdf_chat_prompt import PDF_CHAT_PROMPT
from utils.symptoms import extract_symptoms
from utils.storage import load_data, save_data, DATA_FILE
from llm.router import get_llm_response


# ---------- LOAD ENV ----------
load_dotenv()

if not os.getenv("GEMINI_API_KEY"):
    st.error("❌ GEMINI_API_KEY not found in .env file")
    st.stop()


# ---------- SESSION STATE INIT ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "severity_trend" not in st.session_state:
    st.session_state.severity_trend = load_data()


# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="AI Medical Assistant",
    page_icon="🩺",
    layout="centered"
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

# ---------- SIDEBAR ----------
st.sidebar.markdown("## 🩺 AI Medical Assistant")

if st.sidebar.button("➕ New Chat", use_container_width=True):
    st.session_state.messages = []
    st.rerun()

st.sidebar.markdown("---")

st.sidebar.markdown("## 🧭 Navigation")
page = st.sidebar.radio(
    "Go to",
    ["Medical Assistant", "Health Dashboard", "Medical Report Explainer"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")

st.sidebar.markdown("## ⚙️ Controls")

@st.dialog("⚠️ Delete All Data?")
def clear_all_data():
    st.warning("This will permanently delete chat history and dashboard data.")
    if st.button("Yes, Delete Everything", type="primary"):
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        st.session_state.messages = []
        st.session_state.severity_trend = []
        st.rerun()

if st.sidebar.button("🗑️ Clear All Data", use_container_width=True):
    clear_all_data()

st.sidebar.markdown("---")
st.sidebar.info("⚠️ Educational use only")



# ===============================
# MEDICAL ASSISTANT
# ===============================
if page == "Medical Assistant":

    st.subheader("🧠 Medical Consultant Chat")

    # Show chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    col1, col2, _ = st.columns([0.25, 0.1, 0.7])

    image_data = None
    with col1:
        with st.popover("📎 Add Image"):
            uploaded_image = st.file_uploader(
                "Upload image",
                type=["jpg", "jpeg", "png"],
                label_visibility="collapsed"
            )
            if uploaded_image:
                image_data = Image.open(uploaded_image)
                st.image(image_data, width=200)

    retry = False
    with col2:
        if st.session_state.messages and st.button("↺"):
            retry = True

    if retry:
        if st.session_state.messages[-1]["role"] == "assistant":
            st.session_state.messages.pop()

        with st.spinner("Generating response..."):
            answer = get_llm_response(
                SYSTEM_PROMPT,
                st.session_state.messages,
                image_data
            )
            st.session_state.messages.append(
                {"role": "assistant", "content": answer}
            )
            st.rerun()

    if prompt := st.chat_input("Describe your symptoms..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Analyzing..."):
            answer = get_llm_response(
                SYSTEM_PROMPT,
                st.session_state.messages,
                image_data
            )

            st.session_state.messages.append(
                {"role": "assistant", "content": answer}
            )

            with st.chat_message("assistant"):
                st.markdown(answer)

            symptoms = extract_symptoms(prompt)
            st.session_state.severity_trend.append(len(symptoms))
            save_data(st.session_state.severity_trend)
            st.rerun()


# ===============================
# HEALTH DASHBOARD
# ===============================
elif page == "Health Dashboard":

    st.subheader("📈 Health Analysis Dashboard")

    if not st.session_state.severity_trend:
        st.info("No data yet. Start a medical chat first.")
        st.stop()

    visits = list(range(1, len(st.session_state.severity_trend) + 1))
    severity = st.session_state.severity_trend

    c1, c2, c3 = st.columns(3)
    c1.metric("Consultations", len(visits))
    c2.metric("Latest Severity", severity[-1])
    c3.metric("Health Status", "Stable" if severity[-1] <= 2 else "Needs Attention")

    fig, ax = plt.subplots()
    ax.plot(visits, severity, marker="o")
    ax.set_xlabel("Consultation")
    ax.set_ylabel("Symptom Count")
    ax.grid(alpha=0.3)
    st.pyplot(fig)


# ===============================
# MEDICAL REPORT EXPLAINER
# ===============================
elif page == "Medical Report Explainer":

    st.subheader("📄 Medical Report Explanation")

    if "report_messages" not in st.session_state:
        st.session_state.report_messages = []

    uploaded_file = st.file_uploader("Upload PDF report", type="pdf")

    if uploaded_file:
        reader = PdfReader(uploaded_file)
        report_text = "".join(p.extract_text() or "" for p in reader.pages)
        report_text = report_text[:12000]

        if not st.session_state.report_messages:
            if st.button("Explain Report"):
                with st.spinner("Analyzing report..."):
                    history = [{"role": "user", "content": report_text}]
                    explanation = get_llm_response(PDF_PROMPT, history)
                    st.session_state.report_messages = [
                        {"role": "assistant", "content": explanation}
                    ]
                    st.rerun()

        for msg in st.session_state.report_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if st.session_state.report_messages:
            if q := st.chat_input("Ask a follow-up question..."):
                st.session_state.report_messages.append(
                    {"role": "user", "content": q}
                )

                with st.spinner("Answering..."):
                    ans = get_llm_response(
                        PDF_CHAT_PROMPT,
                        st.session_state.report_messages
                    )
                    st.session_state.report_messages.append(
                        {"role": "assistant", "content": ans}
                    )
                    st.rerun()

    else:
        st.session_state.report_messages = []


# ---------- FOOTER ----------
st.markdown("---")
st.caption("⚠️ This app is for educational purposes only and not a medical diagnosis.")
