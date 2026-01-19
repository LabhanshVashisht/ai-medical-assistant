import os
import json

DATA_FILE = "health_data.json"

def save_key(key_name, key_value):
    os.environ[key_name] = key_value
    env_file = ".env"
    if not os.path.exists(env_file):
        with open(env_file, "w") as f: f.write("")
        
    with open(env_file, "r") as f: lines = f.readlines()
    
    with open(env_file, "w") as f:
        found = False
        for line in lines:
            if line.startswith(f"{key_name}="):
                f.write(f"{key_name}={key_value}\n")
                found = True
            else:
                f.write(line)
        if not found:
            f.write(f"\n{key_name}={key_value}\n")

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def extract_symptoms(text):
    keywords = [
        "fever", "cough", "pain", "headache", "fatigue",
        "vomiting", "nausea", "dizziness", "breath",
        "infection", "diarrhea", "cold"
    ]
    text = text.lower()
    return [k for k in keywords if k in text]
