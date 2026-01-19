import streamlit as st
import os
from pypdf import PdfReader
from modules.llms import get_llm_response
from modules.prompts import PDF_PROMPT, PDF_CHAT_PROMPT

def render(model_choice, required_key):
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
