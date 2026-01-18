# 🩺 AI Medical Assistant

An AI-powered medical chatbot built with **Streamlit**, **OpenAI**, and **Gemini**, featuring:
- Conversational medical guidance with memory
- Multi-modal analysis (Text & Images)
- Health analysis dashboard with trend visualization
- Medical report (PDF) explanation
- Data persistence for health trends
- Multi-model support (ChatGPT & Google Gemini)

---

## 🚀 Features

- 🧠 **Conversational AI Chatbot** with context memory
- 👁️ **Medical Image Analysis** (rashes, x-rays, etc.) via popup
- 📈 **Health Dashboard** with persistent symptom tracking
- 📄 **Medical Report Explainer** (PDF support)
- ⚙️ **Multi-Model Support** (Switch between ChatGPT & Gemini)
- 🔑 **Secure Key Management** (Auto-save to .env)
- 🛡️ **Data Controls** (Clear history & Reset keys safely)
- ⚠️ **Medical Safety** & educational disclaimers

---

## 🛠️ Tech Stack

- Python
- Streamlit
- OpenAI API
- Google Gemini API
- Matplotlib
- PyPDF
- Pillow (Image Processing)

---

## ⚙️ Installation

```bash
git clone https://github.com/LabhanshVashisht/ai-medical-assistant.git
cd ai-medical-assistant
pip install -r requirements.txt
```

## 🔑 Setup

The app automatically manages your API keys. When you run the app:
1. Select your preferred model (ChatGPT or Gemini)
2. If no API key is found, you will be prompted to enter it securely in the sidebar
3. Keys and preferences are saved locally in a `.env` file

Alternatively, you can manually create a `.env` file:
```env
OPENAI_API_KEY=your_openai_key
GEMINI_API_KEY=your_gemini_key
```

## ▶️ Usage

```bash
python -m streamlit run app.py
```
