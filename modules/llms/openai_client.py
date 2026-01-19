import os
import io
import base64
from openai import OpenAI

def get_chatgpt_response(system, messages_history, image_data=None):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Prepare messages properly
    final_messages = [{"role": "system", "content": system}]
    
    for msg in messages_history:
        role = msg["role"]
        content = msg["content"]
        
        # If it's the last user message and has image
        if role == "user" and image_data and msg == messages_history[-1]:
            user_content = [{"type": "text", "text": content}]
            # image_data expected to be a PIL Image
            buffered = io.BytesIO()
            image_data.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{img_str}"}
            })
            final_messages.append({"role": "user", "content": user_content})
        else:
            final_messages.append({"role": role, "content": content})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=final_messages,
        temperature=0.3
    )
    return response.choices[0].message.content
