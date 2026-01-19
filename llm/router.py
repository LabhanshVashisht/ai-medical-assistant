from llm.gemini_llm import gemini_response

def get_llm_response(system, messages_history, image_data=None):
    return gemini_response(system, messages_history, image_data)
