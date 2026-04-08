import os
from typing import List, Tuple
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import streamlit as st

load_dotenv()

PERSIST_DIR = "chroma_db"
COLLECTION_NAME = "real_estate_research"


@st.cache_resource
def _embeddings():
    """Cached embedding model — loads once, stays in memory."""
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")


def _vectorstore():
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=_embeddings(),
        persist_directory=PERSIST_DIR,
    )


def _chunk_docs(docs: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_documents(docs)


def get_indexed_urls() -> set:
    """Returns the set of URLs already stored in Chroma."""
    try:
        vs = _vectorstore()
        data = vs.get()
        sources = {m.get("source", "") for m in data.get("metadatas", [])}
        return sources
    except Exception:
        return set()


def upsert_urls_text(url_text_pairs: List[Tuple[str, str]]) -> Tuple[int, List[str]]:
    """
    Takes [(url, text), ...], skips already-indexed URLs,
    chunks new ones and stores in Chroma.
    Returns (number of chunks added, list of skipped URLs).
    """
    already_indexed = get_indexed_urls()
    skipped = []
    docs: List[Document] = []

    for url, text in url_text_pairs:
        if url in already_indexed:
            skipped.append(url)
            continue
        if text and text.strip():
            docs.append(Document(page_content=text.strip(), metadata={"source": url}))

    if not docs:
        return 0, skipped

    chunks = _chunk_docs(docs)
    vs = _vectorstore()
    vs.add_documents(chunks)
    return len(chunks), skipped


def answer_question(question: str, k: int = 4) -> Tuple[str, List[str], List[str]]:
    """
    Retrieves top-k chunks, asks Groq LLM.
    Returns (answer, unique_sources, chunk_previews).
    """
    vs = _vectorstore()
    results = vs.similarity_search(question, k=k)

    sources = []
    context_blocks = []
    previews = []

    for d in results:
        src = d.metadata.get("source", "unknown")
        sources.append(src)
        context_blocks.append(f"SOURCE: {src}\nTEXT:\n{d.page_content}")
        previews.append({"source": src, "preview": d.page_content[:300]})

    sources_unique = list(dict.fromkeys(sources))

    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        return "Missing GROQ_API_KEY in .env", sources_unique, previews

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.1,
        groq_api_key=groq_key,
    )

    prompt = f"""
You are an expert Real Estate Research Assistant. Your job is to give accurate,
well-structured answers based strictly on the provided source material.

Rules:
- Use ONLY the context below. Do not use outside knowledge.
- If the context is insufficient, say exactly:
  "I don't have enough information from the provided sources."
- Be concise but thorough.
- Always cite which source supports each point.

Question:
{question}

Context:
{chr(10).join(context_blocks)}

Answer format:
1. A clear 2–4 sentence summary answer.
2. Key points as bullet points (if applicable).
3. End with: "Sources used: [list the source URLs]"
"""
    res = llm.invoke(prompt)
    return res.content.strip(), sources_unique, previews
