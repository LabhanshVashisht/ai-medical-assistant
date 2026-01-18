import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import base64
import io
from PIL import Image
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

def get_llm_response(model, system, messages_history, image_data=None):
    if model == "ChatGPT":
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Prepare messages properly
        final_messages = [{"role": "system", "content": system}]
        
        for msg in messages_history:
            role = msg["role"]
            content = msg["content"]
            
            # If it's the last user message and has image
            if role == "user" and image_data and msg == messages_history[-1]:
                user_content = [{"type": "text", "text": content}]
                # image_data expected to be a PIL Image
                buffered = io.BytesIO()
                image_data.save(buffered, format="JPEG")
                img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img_str}"}
                })
                final_messages.append({"role": "user", "content": user_content})
            else:
                final_messages.append({"role": role, "content": content})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=final_messages,
            temperature=0.3
        )
        return response.choices[0].message.content
        
    elif model == "Gemini":
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model_instance = genai.GenerativeModel('gemini-3-flash-preview')
        
        # Construct chat history for Gemini
        chat_history = []
        # Gemini expects alternate parts or a list of contents.
        # We'll just build a large prompt or use start_chat if we convert properly.
        # Simplest for now: concatenate context + use start_chat if structured
        # Let's map to content format
        
        gemini_messages = []
        
        # Add system prompt as a user message or directive at start
        gemini_messages.append({"role": "user", "parts": [system]})
        gemini_messages.append({"role": "model", "parts": ["Understood. I will act as the medical assistant."]})

        for msg in messages_history:
            role = "user" if msg["role"] == "user" else "model"
            parts = [msg["content"]]
            
            if role == "user" and image_data and msg == messages_history[-1]:
                 parts.append(image_data)
            
            gemini_messages.append({"role": role, "parts": parts})
            
        # Normally start_chat expects history to not include the last message technically if we use send_message
        # But here we are doing a single generation usually.
        # Let's just pass the full list to generate_content? No, generate_content takes a list of parts (single turn) usually unless formatted.
        # Correct way for multi-turn in Gemini:
        
        chat = model_instance.start_chat(history=gemini_messages[:-1])
        last_msg = gemini_messages[-1]
        response = chat.send_message(last_msg["parts"])
        
        return response.text
    return "Error: No model selected."

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

if "messages" not in st.session_state:
    st.session_state.messages = []

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
if st.sidebar.button("➕ New Chat"):
    st.session_state.messages = []
    st.rerun()

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
st.sidebar.markdown("### 🛑 Danger Zone")
d_col1, d_col2 = st.sidebar.columns(2)

with d_col1.popover("Clear Data", use_container_width=True):
    st.markdown("### ⚠️ Delete All Data?")
    st.warning("This will permanently delete your chat history and health dashboard trends.")
    if st.button("Yes, Delete Everything", type="primary"):
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        st.session_state.severity_trend = []
        st.session_state.messages = []
        st.rerun()

with d_col2.popover("Reset Keys", use_container_width=True):
    st.markdown("### 🔑 Reset API Keys?")
    st.info("This will remove your saved API keys from the application. You will need to enter them again.")
    if st.button("Confirm Reset"):
        # Clear keys from .env
        if os.path.exists(".env"):
            with open(".env", "r") as f:
                lines = f.readlines()
            with open(".env", "w") as f:
                for line in lines:
                    if not any(k in line for k in ["OPENAI_API_KEY", "GEMINI_API_KEY", "SELECTED_MODEL"]):
                        f.write(line)
        # Clear env vars
        for key in ["OPENAI_API_KEY", "GEMINI_API_KEY", "SELECTED_MODEL"]:
            if key in os.environ:
                del os.environ[key]
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("⚠️ Educational use only")

# ===============================
# MEDICAL ASSISTANT
# ===============================
if page == "Medical Assistant":

    st.subheader("🧠 Medical Consultant Chat")

    # Describe Symptoms Input (Standard Chat Interface)
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Image Uploader (Popup)
    image_data = None
    with st.popover("📎 Add Image"):
        st.markdown("### Upload Medical Image")
        uploaded_image = st.file_uploader(
            "Upload Image", 
            type=["jpg", "jpeg", "png"], 
            key="chat_image",
            label_visibility="collapsed"
        )
        
        if uploaded_image:
            image_data = Image.open(uploaded_image)
            st.image(image_data, caption="Image Preview", width=200)

    # Chat Input
    if prompt := st.chat_input("Describe symptoms..."):
        
        # Add User Message to History
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        if not model_choice:
            st.error("Please select a model in the sidebar.")
        else:
            with st.spinner(f"Analyzing with {model_choice}..."):
                if not os.getenv(required_key):
                    st.error(f"Please set the {model_choice} API key in the sidebar.")
                else:
                    try:
                        # Call LLM with full history
                        answer = get_llm_response(
                            model_choice, 
                            SYSTEM_PROMPT, 
                            st.session_state.messages, 
                            image_data
                        )
                        
                        # Add Assistant Message to History
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                        with st.chat_message("assistant"):
                            st.markdown(answer)

                        # ---- analytics ----
                        # Only extract from latest prompt for trend
                        symptoms = extract_symptoms(prompt)                            
                        st.session_state.severity_trend.append(len(symptoms))
                        save_data(st.session_state.severity_trend)
                        
                    except Exception as e:
                        error_msg = str(e)
                        if "insufficient_quota" in error_msg:
                            st.error("🚨 OpenAI API Quota Exceeded. Please check your billing details or switch to Gemini.")
                        elif "429" in error_msg:
                            st.error("🚨 Gemini API Rate Limit Exceeded. You are strictly rate-limited on the free tier. Please wait a minute or use another model.")
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
                            # Use list format for compatibility with new get_llm_response signature
                            explanation = get_llm_response(model_choice, PDF_PROMPT, [{"role": "user", "content": extracted_text[:12000]}])

                            with st.container(border=True):
                                st.subheader("🧾 Report Explanation")
                                st.write(explanation)
                        except Exception as e:
                            error_msg = str(e)
                            if "insufficient_quota" in error_msg:
                                st.error("🚨 OpenAI API Quota Exceeded. Please check your billing details or switch to Gemini.")
                            elif "429" in error_msg:
                                st.error("🚨 Gemini API Rate Limit Exceeded. You are strictly rate-limited on the free tier. Please wait a minute or use another model.")
                            else:
                                st.error(f"An error occurred: {e}")

# ---------- FOOTER ----------
st.markdown("---")
st.caption(
    "⚠️ This application is for educational purposes only and does not replace professional medical advice."
)
