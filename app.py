import streamlit as st
from dotenv import load_dotenv
import os

# Import custom modules
from modules.utils import save_key, load_data, DATA_FILE
from modules.pages import medical_assistant, health_dashboard, report_explainer

# ---------- LOAD ENV ----------
env_path = ".env"
if not os.path.exists(env_path):
    with open(env_path, "w") as f:
        f.write("")
load_dotenv()

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

# ---------- SESSION STATE ----------
if "severity_trend" not in st.session_state:
    st.session_state.severity_trend = load_data()

if "messages" not in st.session_state:
    st.session_state.messages = []

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
# PAGE ROUTING
# ===============================
if page == "Medical Assistant":
    medical_assistant.render(model_choice, required_key)

elif page == "Health Dashboard":
    health_dashboard.render()

elif page == "Medical Report Explainer":
    report_explainer.render(model_choice, required_key)

# ---------- FOOTER ----------
st.markdown("---")
st.caption(
    "⚠️ This application is for educational purposes only and does not replace professional medical advice."
)
