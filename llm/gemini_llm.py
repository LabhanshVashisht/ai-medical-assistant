import os
import google.generativeai as genai
import streamlit as st




def gemini_response(system_prompt, messages, image=None):
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

    model = genai.GenerativeModel("gemini-2.5-flash")

    parts = [system_prompt]

    for msg in messages:
        if msg["role"] == "user":
            parts.append(msg["content"])
        elif msg["role"] == "assistant":
            parts.append(msg["content"])

    if image:
        parts.append(image)

    try:
        response = model.generate_content(
            parts,
            generation_config={
                
            }
        )

        if not response or not response.text:
            return "I couldn’t generate a proper response. Please try rephrasing."

        return response.text.strip()

    except Exception as e:
        return f"An error occurred while generating the response."
