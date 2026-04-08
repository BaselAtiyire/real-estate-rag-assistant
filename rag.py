import os
from typing import List, Tuple
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

load_dotenv()

PERSIST_DIR = "chroma_db"
COLLECTION_NAME = "real_estate_research"


def _embeddings():
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


def _vectorstore():
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=_embeddings(),
        persist_directory=PERSIST_DIR,
    )


def _chunk_docs(docs: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_documents(docs)


def upsert_urls_text(url_text_pairs: List[Tuple[str, str]]) -> int:
    """
    Takes [(url, text), ...], chunks them, and stores in Chroma.
    Returns number of chunks added.
    """
    docs: List[Document] = []
    for url, text in url_text_pairs:
        if text and text.strip():
            docs.append(Document(page_content=text.strip(), metadata={"source": url}))
    if not docs:
        return 0
    chunks = _chunk_docs(docs)
    vs = _vectorstore()
    vs.add_documents(chunks)
    return len(chunks)


def answer_question(question: str, k: int = 4):
    """
    Retrieves top-k chunks, asks Groq LLM, returns (answer, unique_sources).
    """
    vs = _vectorstore()
    results = vs.similarity_search(question, k=k)

    sources = []
    context_blocks = []
    for d in results:
        src = d.metadata.get("source", "unknown")
        sources.append(src)
        context_blocks.append(f"SOURCE: {src}\nTEXT:\n{d.page_content}")

    sources_unique = list(dict.fromkeys(sources))

    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        return "Missing GROQ_API_KEY in .env", sources_unique

    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0.2,
        groq_api_key=groq_key,
    )

    prompt = f"""
You are a Real Estate Research Assistant.
Use ONLY the context below. If the context is insufficient, say:
"I don't have enough information from the provided sources."

Question:
{question}

Context:
{chr(10).join(context_blocks)}

Answer format:
- 1–4 sentence direct answer
- Optional bullets with key points
"""
    res = llm.invoke(prompt)
    return res.content.strip(), sources_unique
