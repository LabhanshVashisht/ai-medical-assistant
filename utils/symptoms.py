def extract_symptoms(text):
    keywords = [
        "fever", "cough", "pain", "headache", "fatigue",
        "vomiting", "nausea", "dizziness", "breath",
        "infection", "diarrhea", "cold"
    ]
    text = text.lower()
    return [k for k in keywords if k in text]