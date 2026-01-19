from .openai_client import get_chatgpt_response
from .gemini_client import get_gemini_response

def get_llm_response(model, system, messages_history, image_data=None):
    if model == "ChatGPT":
        return get_chatgpt_response(system, messages_history, image_data)
    elif model == "Gemini":
        return get_gemini_response(system, messages_history, image_data)
        
    return "Error: No model selected."
