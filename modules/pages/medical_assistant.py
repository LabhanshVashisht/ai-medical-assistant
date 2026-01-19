import streamlit as st
import os
from PIL import Image
from modules.llms import get_llm_response
from modules.prompts import SYSTEM_PROMPT
from modules.utils import save_data, extract_symptoms

def render(model_choice, required_key):
    st.subheader("🧠 Medical Consultant Chat")

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
