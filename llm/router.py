from llm.openai_llm import openai_response
from llm.gemini_llm import gemini_response

def get_llm_response(model, system, messages_history, image_data=None):
    if model == "ChatGPT":
        return openai_response(system, messages_history, image_data)
    elif model == "Gemini":
        return gemini_response(system, messages_history, image_data)
