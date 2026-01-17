import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from pypdf import PdfReader
import matplotlib.pyplot as plt
import google.generativeai as genai

# ---------- LOAD ENV ----------
env_path = ".env"
if not os.path.exists(env_path):
    with open(env_path, "w") as f:
        f.write("")
load_dotenv()

# ---------- HELPER FUNCTIONS ----------
def save_key(key_name, key_value):
    os.environ[key_name] = key_value
    env_file = ".env"
    if not os.path.exists(env_file):
        with open(env_file, "w") as f: f.write("")
        
    with open(env_file, "r") as f: lines = f.readlines()
    
    with open(env_file, "w") as f:
        found = False
        for line in lines:
            if line.startswith(f"{key_name}="):
                f.write(f"{key_name}={key_value}\n")
                found = True
            else:
                f.write(line)
        if not found:
            f.write(f"\n{key_name}={key_value}\n")

def get_llm_response(model, system, user_text):
    if model == "ChatGPT":
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_text}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    elif model == "Gemini":
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model_instance = genai.GenerativeModel('gemini-3-flash-preview')
        response = model_instance.generate_content(system + "\n\n" + user_text)
        return response.text
    return "Error: No model selected."

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
Do not output internal thought processes or reasoning traces.
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
Do not output internal thought processes or reasoning traces.
End with a disclaimer.
"""

# ---------- SESSION STATE & DATA PERSISTENCE ----------
DATA_FILE = "health_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

if "severity_trend" not in st.session_state:
    st.session_state.severity_trend = load_data()

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
st.sidebar.markdown("## ⚙️ Model Settings")

# Check available keys to set default
has_openai = os.getenv("OPENAI_API_KEY") is not None
has_gemini = os.getenv("GEMINI_API_KEY") is not None
saved_model = os.getenv("SELECTED_MODEL")

# Determine default selection
if saved_model == "ChatGPT":
    default_idx = 0
elif saved_model == "Gemini":
    default_idx = 1
elif has_gemini and not has_openai:
    default_idx = 1
elif has_openai:
    default_idx = 0
else:
    default_idx = None

model_choice = st.sidebar.radio("Select Model", ["ChatGPT", "Gemini"], index=default_idx)

if model_choice:
    # Save selection if changed
    if model_choice != saved_model:
        save_key("SELECTED_MODEL", model_choice)
        
    required_key = "OPENAI_API_KEY" if model_choice == "ChatGPT" else "GEMINI_API_KEY"
    if not os.getenv(required_key):
        st.sidebar.warning(f"⚠️ {model_choice} Key Missing")
        user_key = st.sidebar.text_input(f"Enter Key", type="password")
        if user_key:
            save_key(required_key, user_key)
            st.rerun()
else:
    required_key = None
    st.sidebar.info("Please select a model to continue.")

st.sidebar.markdown("---")
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
            if not model_choice:
                st.error("Please select a model in the sidebar.")
            else:
                with st.spinner(f"Analyzing symptoms with {model_choice}..."):
                    if not os.getenv(required_key):
                        st.error(f"Please set the {model_choice} API key in the sidebar.")
                    else:
                        try:
                            answer = get_llm_response(model_choice, SYSTEM_PROMPT, user_input)
                            
                            with st.container(border=True):
                                st.subheader("🩺 Medical Insight")
                                st.write(answer)

                            # ---- analytics ----
                            symptoms = extract_symptoms(user_input)
                            st.session_state.severity_trend.append(len(symptoms))
                            save_data(st.session_state.severity_trend)
                        except Exception as e:
                            error_msg = str(e)
                            if "insufficient_quota" in error_msg:
                                st.error("🚨 OpenAI API Quota Exceeded. Please check your billing details or switch to Gemini.")
                            else:
                                st.error(f"An error occurred: {e}")
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
            if not model_choice:
                st.error("Please select a model in the sidebar.")
            else:
                with st.spinner(f"Analyzing report with {model_choice}..."):
                    if not os.getenv(required_key):
                        st.error(f"Please set the {model_choice} API key in the sidebar.")
                    else:
                        try:
                            explanation = get_llm_response(model_choice, PDF_PROMPT, extracted_text[:12000])

                            with st.container(border=True):
                                st.subheader("🧾 Report Explanation")
                                st.write(explanation)
                        except Exception as e:
                            error_msg = str(e)
                            if "insufficient_quota" in error_msg:
                                st.error("🚨 OpenAI API Quota Exceeded. Please check your billing details or switch to Gemini.")
                            else:
                                st.error(f"An error occurred: {e}")

# ---------- FOOTER ----------
st.markdown("---")
st.caption(
    "⚠️ This application is for educational purposes only and does not replace professional medical advice."
)
