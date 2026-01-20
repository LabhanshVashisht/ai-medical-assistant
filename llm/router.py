from llm.gemini_llm import gemini_response

def get_llm_response(system_prompt, messages, image=None):
    return gemini_response(system_prompt, messages, image)
