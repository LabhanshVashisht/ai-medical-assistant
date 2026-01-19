import os
import google.generativeai as genai

def get_gemini_response(system, messages_history, image_data=None):
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model_instance = genai.GenerativeModel('gemini-3-flash-preview')
    
    # Construct chat history for Gemini
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
        
    chat = model_instance.start_chat(history=gemini_messages[:-1])
    last_msg = gemini_messages[-1]
    
    # Safety settings to prevent over-blocking medical content
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    try:
        response = chat.send_message(last_msg["parts"], safety_settings=safety_settings)
        return response.text
    except Exception as e:
        # Re-raise exception so caller can handle rate limits (429) vs other errors
        raise e
