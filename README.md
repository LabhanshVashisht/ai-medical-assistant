# 🩺 AI Medical Assistant

An AI-powered medical assistant built with **Streamlit**, **OpenAI**, and **Gemini**, featuring:
- Expert medical guidance (educational use)
- Multi-modal analysis (Text & Images)
- Health analysis dashboard with trend visualization
- Medical report (PDF) explanation
- Data persistence for health trends
- Multi-model support (ChatGPT & Google Gemini)

---

## 🚀 Features

- 🧠 AI medical assistant (non-diagnostic)
- 👁️ Medical image analysis (rashes, x-rays, etc.)
- 📈 Health analysis dashboard with persistent tracking
- 📄 Medical report PDF explanation
- ⚙️ Dynamic model switching (ChatGPT / Gemini)
- 🔑 In-app API key management
- ⚠️ Medical safety & disclaimers

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
