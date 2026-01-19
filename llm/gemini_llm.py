import google.generativeai as genai
import os

def gemini_response(system, messages_history, image_data=None):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model_instance = genai.GenerativeModel('gemini-2.5-flash')
        
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
        
        # Safety settings to prevent over-blocking medical content
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        try:
            response = chat.send_message(
                last_msg["parts"],
                generation_config={
                    "max_output_tokens": 400,
                    "temperature": 0.4,
                    "top_p": 0.9
                },
                safety_settings=safety_settings
            )
            return response.text
        except Exception as e:
            # Re-raise exception so caller can handle rate limits (429) vs other errors
            raise e
        return "Error: No model selected."