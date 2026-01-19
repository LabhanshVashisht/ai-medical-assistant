import streamlit as st
from dotenv import load_dotenv
import os
import json
import base64
import io
from PIL import Image
from pypdf import PdfReader
import matplotlib.pyplot as plt
from prompts.system_prompt import SYSTEM_PROMPT
from prompts.pdf_prompt import PDF_PROMPT
from prompts.pdf_chat_prompt import PDF_CHAT_PROMPT
from utils.env_manager import save_key
from utils.symptoms import extract_symptoms
from utils.storage import load_data, save_data
from llm.router import get_llm_response
from utils.storage import DATA_FILE
from prompts.pdf_chat_prompt import PDF_CHAT_PROMPT


# ---------- LOAD ENV ----------
env_path = ".env"
if not os.path.exists(env_path):
    with open(env_path, "w") as f:
        f.write("")
load_dotenv()


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

model_choice = st.sidebar.radio(
    "Select Model", 
    ["ChatGPT", "Gemini"], 
    index=default_idx,
    help="Choose the AI model to power the assistant"
)

if model_choice:
    # Save selection if changed
    if model_choice != saved_model:
        save_key("SELECTED_MODEL", model_choice)
        
    required_key = "OPENAI_API_KEY" if model_choice == "ChatGPT" else "GEMINI_API_KEY"
    if not os.getenv(required_key):
        st.sidebar.warning(f"⚠️ {model_choice} Key Missing")
        user_key = st.sidebar.text_input(f"Enter Key", type="password", help=f"Paste your {model_choice} API Key here")
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
    ["Medical Assistant", "Health Dashboard", "Medical Report Explainer"],
    help="Navigate between Chat, Analytics, and PDF Report features",
    captions=["Chat with AI Doctor", "View Health Trends", "Analyze Medical PDFs"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Settings & Danger Zone")
s_col1, s_col2 = st.sidebar.columns(2)

with s_col1.popover("Change Keys", use_container_width=True, help="Update API Keys"):
    st.markdown("### 🔑 Update API Keys")
    
    # Status Indicators
    st.caption("Current Status:")
    if os.getenv("OPENAI_API_KEY"):
         st.markdown("- ChatGPT: ✅ Set")
    else:
         st.markdown("- ChatGPT: ❌ Not Set")
         
    if os.getenv("GEMINI_API_KEY"):
         st.markdown("- Gemini:  ✅ Set")
    else:
         st.markdown("- Gemini:  ❌ Not Set")
    
    st.markdown("---")
    new_openai = st.text_input("New ChatGPT Key", type="password")
    if st.button("Update ChatGPT Key", type="primary", help="Save new ChatGPT Key"):
        save_key("OPENAI_API_KEY", new_openai)
        st.success("ChatGPT Key Updated!")
        st.rerun()
        
    new_gemini = st.text_input("New Gemini Key", type="password")
    if st.button("Update Gemini Key", type="primary", help="Save new Gemini Key"):
        save_key("GEMINI_API_KEY", new_gemini)
        st.success("Gemini Key Updated!")
        st.rerun()

with s_col2.popover("Reset Keys", use_container_width=True, help="Clear all saved keys"):
    st.markdown("### 🔑 Reset API Keys?")
    st.info("This will remove your saved API keys from the application. You will need to enter them again.")
    if st.button("Confirm Reset", type="primary", help="Permanently remove saved keys"):
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

# Clear Data Button (Red, Full Width below keys)
@st.dialog("⚠️ Delete All Data?")
def show_clear_data_dialog():
    st.warning("This will permanently delete your chat history and health dashboard trends.")
    if st.button("Yes, Delete Everything", type="primary", help="Confirm permanent deletion"):
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        st.session_state.severity_trend = []
        st.session_state.messages = []
        st.rerun()

if st.sidebar.button("🗑️ Clear All Data", type="primary", use_container_width=True, help="Permanently delete all history"):
    show_clear_data_dialog()

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

    # Action Buttons (Add Image + Retry)
    col1, col2, _ = st.columns([0.25, 0.1, 0.7])
    
    with col1:
        # Image Uploader (Popup)
        image_data = None
        with st.popover("📎 Add Image", use_container_width=True, help="Upload a medical image for analysis"):
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

    trigger_retry = False
    with col2:
        # Regenerate/Retry Button
        if st.session_state.messages:
            last_role = st.session_state.messages[-1]["role"]
            if last_role in ["assistant", "user"]:
                if st.button("↺", help="Regenerate/Retry Response", use_container_width=True):
                    trigger_retry = True

    if trigger_retry:
        last_role = st.session_state.messages[-1]["role"]
        if last_role == "assistant":
            st.session_state.messages.pop()

        with st.spinner(f"Generating with {model_choice}..."):
            if not os.getenv(required_key):
                st.error(f"Please set the {model_choice} API key.")
            else:
                try:
                    answer = get_llm_response(
                        model_choice, 
                        SYSTEM_PROMPT, 
                        st.session_state.messages, 
                        image_data
                    )
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    st.rerun()
                except Exception as e:
                    error_msg = str(e)
                    if "insufficient_quota" in error_msg:
                        st.error("🚨 OpenAI API Quota Exceeded. Please check your billing details or switch to Gemini.")
                    elif "429" in error_msg:
                        st.error("🚨 Gemini API Rate Limit Exceeded. You are strictly rate-limited on the free tier. Please wait a minute or use another model.")
                    else:
                        st.error(f"An error occurred: {e}")

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
                        st.rerun()
                        
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
    
    # Session state for report chat
    if "report_messages" not in st.session_state:
        st.session_state.report_messages = []
    if "last_uploaded_file" not in st.session_state:
        st.session_state.last_uploaded_file = None

    uploaded_file = st.file_uploader(
        "Upload a medical report (PDF)",
        type="pdf"
    )

    if uploaded_file:
        # Check if file changed
        if uploaded_file.file_id != st.session_state.last_uploaded_file:
             st.session_state.report_messages = []
             st.session_state.last_uploaded_file = uploaded_file.file_id
             
        reader = PdfReader(uploaded_file)
        extracted_text = ""
        for p in reader.pages:
            extracted_text += p.extract_text() + "\n"
        
        # Limit text
        report_content = extracted_text[:12000]

        # Initial Explanation Trigger
        if not st.session_state.report_messages:
            if st.button("Explain Report", help="Generate a summary and analysis of the uploaded PDF"):
                if not model_choice:
                    st.error("Please select a model in the sidebar.")
                else:
                    with st.spinner(f"Analyzing report with {model_choice}..."):
                        if not os.getenv(required_key):
                            st.error(f"Please set the {model_choice} API key in the sidebar.")
                        else:
                            try:
                                # Prepare initial message context
                                initial_msg = f"Here is the medical report content:\n\n{report_content}"
                                history = [{"role": "user", "content": initial_msg}]
                                
                                explanation = get_llm_response(model_choice, PDF_PROMPT, history)
                                
                                # Store in history
                                st.session_state.report_messages.append({"role": "user", "content": initial_msg})
                                st.session_state.report_messages.append({"role": "assistant", "content": explanation})
                                st.rerun()

                            except Exception as e:
                                error_msg = str(e)
                                if "insufficient_quota" in error_msg:
                                    st.error("🚨 OpenAI API Quota Exceeded. Please check your billing details or switch to Gemini.")
                                elif "429" in error_msg:
                                    st.error("🚨 Gemini API Rate Limit Exceeded. Please wait a minute.")
                                else:
                                    st.error(f"An error occurred: {e}")

        # Display Chat History
        for i, message in enumerate(st.session_state.report_messages):
            if i == 0: 
                # Hide the massive report text from UI, just show a confirmation
                with st.chat_message("user"):
                    st.markdown("📄 **Uploaded Medical Report**")
            else:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        # Chat Input for Follow-up
        if st.session_state.report_messages:
            if prompt := st.chat_input("Ask a follow-up question about this report..."):
                
                st.session_state.report_messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                if not model_choice:
                    st.error("Please select a model.")
                else:
                    with st.spinner(f"Answering with {model_choice}..."):
                        try:
                            answer = get_llm_response(
                                model_choice, 
                                PDF_CHAT_PROMPT, 
                                st.session_state.report_messages
                            )
                            
                            st.session_state.report_messages.append({"role": "assistant", "content": answer})
                            with st.chat_message("assistant"):
                                st.markdown(answer)
                        except Exception as e:
                             st.error(f"Error: {e}")

    else:
        # Clear specific history if no file
        st.session_state.report_messages = []
        st.session_state.last_uploaded_file = None

# ---------- FOOTER ----------
st.markdown("---")
st.caption(
    "⚠️ This application is for educational purposes only and does not replace professional medical advice."
)
