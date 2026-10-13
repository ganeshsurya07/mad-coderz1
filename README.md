# 🩺 AI-Powered Personal Health Copilot

An AI-powered healthcare assistant designed to help people understand, organize, and manage their medical information in one place. The application analyzes uploaded medical documents and provides easy-to-understand summaries, health insights, and an interactive AI chat experience.

## 🚀 Project Overview

Medical information is often scattered across laboratory reports, prescriptions, and other healthcare documents. Understanding these records can be difficult for many people.

The **AI-Powered Personal Health Copilot** aims to simplify this process by bringing medical documents together in a single interface and using AI to help users better understand the information they contain.

## ✨ Key Features

* **Medical Document Analysis:** Upload medical documents for AI-powered analysis.
* **Health Summary:** View key information extracted from uploaded reports.
* **Document History:** Review previously processed documents during the current session.
* **AI Health Copilot:** Ask questions about your medical documents through an interactive chat interface.
* **Multilingual Support:** Access the application in English or Telugu.
* **Exportable Records:** Download available health information in JSON format.
* **Simple User Interface:** Navigate between document uploads, health overviews, history, and AI assistance.

## 🛠️ Tech Stack

* **Python** — Core programming language
* **Streamlit** — Interactive web application
* **Groq API** — AI-powered text analysis and chat
* **PyPDF** — PDF text extraction
* **Tesseract OCR** — Text extraction from supported medical document images

## ⚙️ How It Works

1. Upload a medical report or supported document.
2. Extract text from the uploaded document.
3. Process the extracted information using an AI model.
4. Display the generated summary and relevant insights.
5. Ask follow-up questions using the AI Copilot.
6. Review available records and export information when needed.

## 💻 Run Locally

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd health-copilot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API credentials

Create a `.streamlit/secrets.toml` file and add your Groq API configuration:

```toml
GROQ_API_KEY = "your_groq_api_key"
GROQ_MODEL = "openai/gpt-oss-120b"
```

Never commit your API key or secrets file to GitHub.

### 4. Start the application

```bash
streamlit run app.py
```

## 🌐 Live Demo

**Live Application:** YOUR_DEPLOYED_STREAMLIT_URL

## 🔒 Privacy and Responsible Use

This application is a prototype intended to assist with understanding medical information. AI-generated outputs may be incomplete or inaccurate and should not replace professional medical advice, diagnosis, or treatment.

Avoid uploading sensitive medical information unless you understand how the application and its AI provider process data. Do not use the application for emergency medical decisions.

## 🔮 Future Enhancements

* Persistent storage for health records
* Improved document organization and search
* More detailed report comparisons over time
* Additional Indian language support
* Stronger privacy controls and secure authentication
* More reliable medical information extraction and validation

## 👨‍💻 Built For

A hackathon project exploring how AI can make healthcare information easier to understand and manage.

---

**AI-Powered Personal Health Copilot** — Making medical information easier to understand, one report at a time.
