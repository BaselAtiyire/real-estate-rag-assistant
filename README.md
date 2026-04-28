# 🏡 Real Estate RAG Assistant

> A Retrieval-Augmented Generation (RAG) web app that ingests real estate news and articles, builds a semantic knowledge base with vector embeddings, and answers user questions with source citations using an LLM.

**Live Demo:** [baselatiyire-real-estate-rag-assistant-app-ejmnhc.streamlit.app](https://baselatiyire-real-estate-rag-assistant-app-ejmnhc.streamlit.app/)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔗 **URL Ingestion** | Paste real estate article URLs to index content |
| 🧠 **RAG Pipeline** | Chunking + embeddings + vector search via ChromaDB |
| 💬 **LLM Q&A with Citations** | Answers grounded in retrieved sources using Groq |
| 🔁 **Demo vs Custom Mode** | Preloaded demo sources or user-provided URLs |
| 🧹 **Reset Knowledge Base** | Clear and re-index your sources anytime |
| 🔐 **Secrets Safe** | API keys handled via environment variables / Streamlit Secrets |

---

## 🧱 Architecture

```
URLs
 └─► Text Extraction (trafilatura)
      └─► Chunking
           └─► Embeddings (sentence-transformers / MiniLM)
                └─► ChromaDB (Vector Store)
                     └─► Similarity Search
                          └─► Groq LLM (llama-3.1-8b-instant)
                               └─► Answer + Source Citations
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Streamlit |
| **LLM** | Groq (`llama-3.1-8b-instant`) |
| **Vector Database** | ChromaDB |
| **Embeddings** | sentence-transformers (MiniLM) |
| **Text Extraction** | trafilatura + requests |
| **Language** | Python 3.11+ |

---

## 🚀 Getting Started (Local)

### 1. Clone the Repository

```bash
git clone https://github.com/BaselAtiyire/real-estate-rag-assistant.git
cd real-estate-rag-assistant
```

### 2. Create & Activate a Virtual Environment

Python 3.11 is recommended.

```bash
python -m venv .venv

# Windows
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Your API Key

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

> ⚠️ **Never commit your `.env` file.** It is already listed in `.gitignore`.

### 5. Run the App

```bash
streamlit run app.py
```

Open your browser at: [http://localhost:8501](http://localhost:8501)

---

## 🌐 Deploy to Streamlit Community Cloud

1. Go to [Streamlit Community Cloud](https://streamlit.io/cloud) → **New app**
2. Set the following:
   - **Repo:** `BaselAtiyire/real-estate-rag-assistant`
   - **Branch:** `main`
   - **Main file path:** `app.py`
   - **Python version:** 3.11 or 3.12
3. Under **Secrets**, add:
   ```toml
   GROQ_API_KEY = "YOUR_GROQ_API_KEY"
   ```
4. Click **Deploy**

---

## 🧪 Example Questions

Once the knowledge base is loaded, try asking:

- *How do rising interest rates affect monthly mortgage payments?*
- *Why did the Modesto house go viral on Zillow?*
- *Which U.S. housing markets are considered "up-and-coming" and why?*

---

## 📁 Project Structure

```
.
├── app.py            # Streamlit UI
├── ingest.py         # URL text extraction
├── rag.py            # RAG pipeline (ChromaDB + Groq)
├── requirements.txt  # Python dependencies
├── .gitignore        # Ignores venv, secrets, local DB
└── README.md
```

---

## 🔒 Security

- API keys are **never** committed to the repository.
- Use `.env` locally and **Streamlit Secrets** in production.
- If a key was ever accidentally committed, rotate it immediately.

---

## 📌 Roadmap

- [ ] PDF upload & ingestion
- [ ] Chat-style conversational memory
- [ ] Show retrieved chunks for explainability
- [ ] Add evaluation metrics (top-k relevance, latency)

---

## 📄 License

This project is open source. See [LICENSE](LICENSE) for details.
