import os
import shutil
import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="Real Estate Research Tool",
    layout="wide",
    page_icon="🏠",
)

# ---- Custom CSS ----
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
    .answer-box {
        background-color: #ffffff;
        border-left: 4px solid #2e86de;
        padding: 1.2rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .source-chip {
        background-color: #eaf0fb;
        border-radius: 20px;
        padding: 4px 12px;
        font-size: 0.8rem;
        margin: 4px;
        display: inline-block;
    }
    .preview-box {
        background-color: #f1f3f5;
        border-radius: 6px;
        padding: 0.8rem;
        font-size: 0.85rem;
        color: #444;
        margin-bottom: 0.5rem;
    }
    .chat-question {
        background-color: #2e86de;
        color: white;
        padding: 0.6rem 1rem;
        border-radius: 12px 12px 0 12px;
        margin-bottom: 0.3rem;
        font-weight: 600;
    }
    .chat-answer {
        background-color: #ffffff;
        border: 1px solid #ddd;
        padding: 0.6rem 1rem;
        border-radius: 0 12px 12px 12px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ---- Header ----
st.markdown("# 🏠 Real Estate Research Tool")
st.caption("Index real estate articles → ask questions → get AI answers with citations.")

# ---- Safe imports ----
try:
    from ingest import fetch_url_text
    from rag import upsert_urls_text, answer_question, PERSIST_DIR, get_indexed_urls
except Exception as e:
    st.error("❌ Import error (app could not start).")
    st.exception(e)
    st.stop()

# ---- Demo URLs ----
DEFAULT_URLS = [
    "https://www.yahoo.com/lifestyle/articles/modesto-house-featured-zillow-gone-222629056.html?fr=yhssrp_catchall",
    "https://www.realestateagents.com/blog/all/how-do-rising-interest-rates-impact-your-mortgage-payment",
    "https://finance.yahoo.com/news/america-10-best-coming-housing-130048898.html?fr=yhssrp_catchall",
]


def reset_vector_db():
    if os.path.exists(PERSIST_DIR):
        shutil.rmtree(PERSIST_DIR, ignore_errors=True)


def run_ingest(urls):
    pairs = []
    bad = []
    progress = st.progress(0)
    total = max(len(urls), 1)

    for idx, u in enumerate(urls, start=1):
        text = fetch_url_text(u)
        if not text or len(text) < 250:
            bad.append(u)
        pairs.append((u, text))
        progress.progress(int(idx / total * 100))

    good = [(u, t) for (u, t) in pairs if t and len(t) >= 250]
    added_chunks, skipped = upsert_urls_text(good)
    return added_chunks, [u for (u, _) in good], bad, skipped


# ---- Session State ----
if "ready" not in st.session_state:
    st.session_state.ready = False
if "last_sources" not in st.session_state:
    st.session_state.last_sources = []
if "last_ingest_summary" not in st.session_state:
    st.session_state.last_ingest_summary = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    st.markdown("## ⚙️ Settings")

    mode = st.radio(
        "Source mode",
        ["Demo (preloaded URLs)", "Custom (paste your own URLs)"],
        index=0,
    )

    if mode == "Demo (preloaded URLs)":
        urls = DEFAULT_URLS
        st.markdown("**Demo URLs:**")
        for i, u in enumerate(urls, start=1):
            st.caption(f"URL {i}: {u[:60]}...")
    else:
        url1 = st.text_input("URL 1", placeholder="https://...")
        url2 = st.text_input("URL 2", placeholder="https://...")
        url3 = st.text_input("URL 3", placeholder="https://...")
        urls = [u.strip() for u in [url1, url2, url3] if u and u.strip()]

    st.divider()
    k = st.slider("Top-k chunks to retrieve", min_value=2, max_value=10, value=4)

    st.divider()
    colA, colB = st.columns(2)
    with colA:
        process = st.button("🔄 Process URLs", use_container_width=True)
    with colB:
        clear_db = st.button("🗑️ Clear KB", use_container_width=True)

    st.divider()

    # Show indexed URLs
    st.markdown("### 📚 Indexed Sources")
    indexed = get_indexed_urls()
    if indexed:
        for u in indexed:
            st.caption(f"✅ {u[:55]}...")
    else:
        st.caption("Nothing indexed yet.")

    st.divider()
    st.markdown("### 🔑 API Status")
    if os.getenv("GROQ_API_KEY"):
        st.success("GROQ_API_KEY ✅")
    else:
        st.error("GROQ_API_KEY missing ❌")


# ==============================
# CLEAR DB
# ==============================
if clear_db:
    reset_vector_db()
    st.session_state.ready = False
    st.session_state.last_sources = []
    st.session_state.chat_history = []
    st.session_state.last_ingest_summary = "🧹 Knowledge base cleared."
    st.toast("Cleared knowledge base", icon="🧹")


# ==============================
# PROCESS URLs
# ==============================
if process:
    if not urls:
        st.warning("Add at least one URL.")
    else:
        with st.spinner("Fetching & indexing sources..."):
            added_chunks, good_urls, bad_urls, skipped_urls = run_ingest(urls)

        st.session_state.last_sources = good_urls
        st.session_state.ready = added_chunks > 0 or len(get_indexed_urls()) > 0

        lines = []
        if added_chunks > 0:
            lines.append(f"✅ Indexed **{added_chunks}** chunks from **{len(good_urls)}** source(s).")
        if skipped_urls:
            lines.append(f"⏭️ Skipped **{len(skipped_urls)}** already-indexed URL(s).")
        if bad_urls:
            lines.append("⚠️ Could not extract text from:")
            lines.extend([f"- {u}" for u in bad_urls])
        if not lines:
            lines.append("ℹ️ No new content to index.")

        st.session_state.last_ingest_summary = "\n".join(lines)
        st.rerun()

if st.session_state.last_ingest_summary:
    st.info(st.session_state.last_ingest_summary)

st.divider()

# ==============================
# Q&A SECTION
# ==============================
col_main, col_history = st.columns([3, 2])

with col_main:
    st.markdown("## 💬 Ask a Question")
    question = st.text_input(
        "Your question",
        placeholder="e.g., How do rising interest rates affect mortgage payments?",
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        ask = st.button("🔍 Get Answer", use_container_width=True)
    with col2:
        clear_chat = st.button("🗑️ Clear Chat History", use_container_width=True)

    if clear_chat:
        st.session_state.chat_history = []
        st.toast("Chat history cleared", icon="🗑️")

    if ask:
        if not question.strip():
            st.warning("Type a question first.")
        elif not st.session_state.ready and not get_indexed_urls():
            st.warning("No sources indexed yet. Click **Process URLs** first.")
        elif not os.getenv("GROQ_API_KEY"):
            st.error("Missing GROQ_API_KEY.")
        else:
            with st.spinner("Searching sources and generating answer..."):
                answer, sources, previews = answer_question(question.strip(), k=k)

            # Save to chat history
            st.session_state.chat_history.append({
                "question": question.strip(),
                "answer": answer,
                "sources": sources,
                "previews": previews,
                "time": datetime.now().strftime("%H:%M:%S"),
            })
            st.session_state.ready = True

    # Show latest answer
    if st.session_state.chat_history:
        latest = st.session_state.chat_history[-1]

        st.markdown("### 📝 Answer")
        st.markdown(
            f'<div class="answer-box">{latest["answer"]}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("### 🔗 Sources")
        for s in latest["sources"]:
            st.markdown(f'<span class="source-chip">🔗 {s}</span>', unsafe_allow_html=True)

        st.markdown("### 🔍 Chunk Previews")
        for p in latest["previews"]:
            with st.expander(f"📄 {p['source'][:80]}..."):
                st.markdown(
                    f'<div class="preview-box">{p["preview"]}...</div>',
                    unsafe_allow_html=True,
                )

        # Export answer as text file
        st.divider()
        export_text = f"""Real Estate Research Tool - Export
Time: {latest['time']}

Question:
{latest['question']}

Answer:
{latest['answer']}

Sources:
{chr(10).join(latest['sources'])}
"""
        st.download_button(
            label="⬇️ Export Answer as TXT",
            data=export_text,
            file_name=f"answer_{latest['time'].replace(':', '-')}.txt",
            mime="text/plain",
            use_container_width=True,
        )


# ==============================
# CHAT HISTORY PANEL
# ==============================
with col_history:
    st.markdown("## 📜 Chat History")
    if not st.session_state.chat_history:
        st.caption("No questions asked yet.")
    else:
        for i, entry in enumerate(reversed(st.session_state.chat_history), start=1):
            st.markdown(
                f'<div class="chat-question">Q: {entry["question"]}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="chat-answer">{entry["answer"][:300]}{"..." if len(entry["answer"]) > 300 else ""}</div>',
                unsafe_allow_html=True,
            )
            st.caption(f"🕐 {entry['time']}")
            if i < len(st.session_state.chat_history):
                st.divider()
