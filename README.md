# LUX - Local AI Knowledge Assistant

<div align="center">
  <img src="ui/lux_logo.png" alt="LUX Logo" width="120" />
</div>

<p align="center">
  A completely local, offline, and privacy-first Retrieval-Augmented Generation (RAG) AI Assistant powered by <strong>Microsoft Foundry Local</strong>.
</p>

## 🌟 Overview

LUX is a powerful local AI assistant that allows you to chat with your own documents without sending any data to the cloud. By utilizing the Microsoft Foundry Local SDK, it runs advanced Large Language Models (LLMs) and Vector Embedding models directly on your hardware.

### Key Features
- **100% Privacy**: Everything runs locally. No internet connection required after the initial model download.
- **RAG Architecture**: Ingests your Markdown, TXT, or PDF documents, chunks them, and stores them in a local SQLite vector database.
- **Modern UI**: A sleek, responsive, glassmorphism-inspired web interface with customizable themes.
- **Source Transparency**: Every answer includes the exact file names and similarity scores used to generate the response.
- **Conversation History**: Seamlessly save, load, and switch between your chat histories.

## 🛠️ Technology Stack
- **Backend**: FastAPI (Python)
- **Local AI Provider**: Microsoft Foundry Local SDK
- **Language Model**: `phi-3.5-mini`
- **Embedding Model**: `qwen3-embedding-0.6b`
- **Database**: SQLite (No external vector DB required!)
- **Frontend**: Vanilla HTML/CSS/JS

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- Microsoft Foundry Local installed on your machine
- Foundry Local API Key

### 2. Installation
Clone the repository and install the required dependencies:

```bash
git clone https://github.com/yourusername/lux.git
cd lux
pip install -r requirements.txt
```

### 3. Environment Setup
Rename `.env.example` to `.env` and add your Foundry Local endpoint and API key:

```env
FOUNDRY_LOCAL_ENDPOINT="http://localhost:60591"
FOUNDRY_LOCAL_API_KEY="your-api-key-here"
```

### 4. Ingesting Documents
Place your documents (e.g., `popular_science.md`) inside the `documents` folder. Then, run the ingestion script to build the vector database:

```bash
python scripts/ingest.py
```

### 5. Running the Application
Start the backend server and UI:

```bash
python -m app.main
```
Open your browser and navigate to **[http://localhost:8000](http://localhost:8000)** to start chatting!

---

## 🖼️ UI Previews
*(Add your screenshots here)*

## 🤝 Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

## 📝 License
This project is open-source and available under the MIT License.
