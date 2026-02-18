🏡 Real Estate RAG Assistant

A Retrieval-Augmented Generation (RAG) web app that ingests real estate news/articles, builds a semantic knowledge base with vector embeddings, and answers user questions with source citations using an LLM. Built with Streamlit, ChromaDB, and Groq.

Live Demo: https://baselatiyire-real-estate-rag-assistant-app-ejmnhc.streamlit.app/

✨ Features

🔗 URL Ingestion – Paste real estate article URLs to index content

🧠 RAG Pipeline – Chunking + embeddings + vector search (ChromaDB)

💬 LLM Q&A with Citations – Answers grounded in retrieved sources (Groq)

🔁 Demo vs Custom Mode – Preloaded demo sources or user-provided URLs

🧹 Reset Knowledge Base – Clear and re-index anytime

🔐 Secrets Safe – API keys handled via environment variables / Streamlit Secrets

🧱 Architecture (High Level)
URLs → Text Extraction → Chunking → Embeddings → ChromaDB (Vector Store)
                                     ↓
                               Similarity Search
                                     ↓
                                 Groq LLM
                                     ↓
                          Answer + Source Citations

🛠️ Tech Stack

Frontend: Streamlit

LLM: Groq (llama-3.1-8b-instant)

Vector DB: ChromaDB

Embeddings: sentence-transformers (MiniLM)

Extraction: trafilatura + requests

Language: Python 3.11+

🚀 Getting Started (Local)
1) Clone the repo
git clone https://github.com/BaselAtiyire/real-estate-rag-assistant.git
cd real-estate-rag-assistant

2) Create & activate a virtual environment (Python 3.11 recommended)
python -m venv .venv
# Windows
.\.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate

3) Install dependencies
pip install -r requirements.txt

4) Set your API key

Create a .env file:

GROQ_API_KEY=your_groq_api_key_here


⚠️ Do not commit .env to GitHub. It’s already in .gitignore.

5) Run the app
streamlit run app.py


Open: http://localhost:8501

🌐 Deploy (Streamlit Community Cloud)

Go to Streamlit Community Cloud → New app

Repo: BaselAtiyire/real-estate-rag-assistant

Branch: main

Main file path: app.py

Python: 3.11 or 3.12

Secrets:

GROQ_API_KEY="YOUR_GROQ_API_KEY"


Click Deploy

🧪 Example Questions

How do rising interest rates affect monthly mortgage payments?

Why did the Modesto house go viral on Zillow?

Which U.S. housing markets are considered “up-and-coming” and why?

📁 Project Structure
.
├─ app.py              # Streamlit UI
├─ ingest.py           # URL text extraction
├─ rag.py              # RAG pipeline (ChromaDB + Groq)
├─ requirements.txt   # Dependencies
├─ .gitignore          # Ignore venv, secrets, local DB
└─ README.md

🔒 Security Notes

API keys are never committed to the repository.

Use .env locally and Streamlit Secrets in production.

If a key was ever committed, rotate it immediately.

📌 Roadmap

 PDF upload & ingestion

 Chat-style conversational memory

 Show retrieved chunks for explainability

 Add evaluation metrics (top-k relevance, latency)
