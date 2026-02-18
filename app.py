import os
import shutil
import streamlit as st

st.set_page_config(page_title="Real Estate Research Tool", layout="wide")
st.title("Real Estate Research Tool")
st.caption("Research real estate articles (RAG) → ask questions → get answers with citations.")

# ---- Safe imports (prevents blank page) ----
try:
    from ingest import fetch_url_text
    from rag import upsert_urls_text, answer_question, PERSIST_DIR
except Exception as e:
    st.error("❌ Import error (app could not start).")
    st.exception(e)
    st.stop()

# --- Preloaded demo URLs (hardcoded) ---
DEFAULT_URLS = [
    "https://www.yahoo.com/lifestyle/articles/modesto-house-featured-zillow-gone-222629056.html?fr=yhssrp_catchall",
    "https://www.realestateagents.com/blog/all/how-do-rising-interest-rates-impact-your-mortgage-payment",
    "https://finance.yahoo.com/news/america-10-best-coming-housing-130048898.html?fr=yhssrp_catchall",
]


def reset_vector_db():
    """Deletes persisted Chroma DB so you can re-index cleanly."""
    if os.path.exists(PERSIST_DIR):
        shutil.rmtree(PERSIST_DIR, ignore_errors=True)


def run_ingest(urls):
    """Fetches text from URLs and indexes into Chroma. Returns (added_chunks, good_urls, bad_urls)."""
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
    added_chunks = upsert_urls_text(good)
    return added_chunks, [u for (u, _) in good], bad


# ---- Session defaults ----
if "ready" not in st.session_state:
    st.session_state.ready = False
if "last_sources" not in st.session_state:
    st.session_state.last_sources = []
if "last_ingest_summary" not in st.session_state:
    st.session_state.last_ingest_summary = ""


with st.sidebar:
    st.subheader("Sources")

    mode = st.radio(
        "Choose source mode",
        ["Demo (preloaded URLs)", "Custom (paste your own URLs)"],
        index=0,
    )

    if mode == "Demo (preloaded URLs)":
        urls = DEFAULT_URLS
        st.markdown("**Demo URLs loaded:**")
        for i, u in enumerate(urls, start=1):
            st.write(f"URL {i}")
            st.code(u)
    else:
        url1 = st.text_input("URL 1", placeholder="https://...")
        url2 = st.text_input("URL 2", placeholder="https://...")
        url3 = st.text_input("URL 3", placeholder="https://...")
        urls = [u.strip() for u in [url1, url2, url3] if u and u.strip()]

    st.divider()
    k = st.slider("Top-k chunks to retrieve", min_value=2, max_value=10, value=4)

    colA, colB = st.columns(2)
    with colA:
        process = st.button("Process URLs", use_container_width=True)
    with colB:
        clear_db = st.button("Clear Knowledge Base", use_container_width=True)

    # ✅ Better auto-ingest UX
    auto_ingest = st.checkbox("Auto-ingest demo sources", value=False)

    if auto_ingest and mode == "Demo (preloaded URLs)":
        st.caption("Auto-ingest is ON (demo mode).")
        run_now = st.button("Run Auto-Ingest Now", use_container_width=True)
    else:
        run_now = False

    st.divider()
    st.subheader("API Key Check")
    if os.getenv("GROQ_API_KEY"):
        st.success("GROQ_API_KEY found ✅")
    else:
        st.warning("GROQ_API_KEY not found. Add it to your .env file.")


# ---- Clear DB ----
if clear_db:
    reset_vector_db()
    st.session_state.ready = False
    st.session_state.last_sources = []
    st.session_state.last_ingest_summary = "🧹 Knowledge base cleared."
    st.toast("Cleared Chroma DB", icon="🧹")


# ---- Auto-ingest trigger (first load) ----
# If auto_ingest is checked, we ingest once unless already ready.
if auto_ingest and mode == "Demo (preloaded URLs)" and not st.session_state.ready:
    # Show an obvious message so it doesn't feel like "nothing happened"
    st.info("Auto-ingest is enabled. Indexing demo sources now…")
    process = True

# ---- Manual "Run Auto-Ingest Now" ----
if run_now:
    process = True

# ---- Process URLs ----
if process:
    if not urls:
        st.warning("Add at least one URL.")
    else:
        with st.spinner("Fetching & indexing sources..."):
            added_chunks, good_urls, bad_urls = run_ingest(urls)

        st.session_state.last_sources = good_urls
        st.session_state.ready = added_chunks > 0

        lines = [f"✅ Indexed **{added_chunks}** chunks from **{len(good_urls)}** source(s)."]
        if bad_urls:
            lines.append("⚠️ Could not extract enough text from:")
            lines.extend([f"- {u}" for u in bad_urls])

        # extra clarity for demo mode
        if mode == "Demo (preloaded URLs)" and st.session_state.ready:
            lines.append("🚀 Demo knowledge base is ready. Ask a question below!")

        st.session_state.last_ingest_summary = "\n".join(lines)


# ---- Status panel ----
if st.session_state.last_ingest_summary:
    st.info(st.session_state.last_ingest_summary)

st.divider()

# ---- Q&A ----
st.subheader("Ask a Question")
question = st.text_input(
    "Ask about the processed sources",
    placeholder="e.g., How do rising interest rates affect mortgage payments?",
)

col1, col2 = st.columns([1, 1])
with col1:
    ask = st.button("Get Answer", use_container_width=True)
with col2:
    st.write("")
    st.write("Tip: Index sources first, then ask questions.")

if ask:
    if not question.strip():
        st.warning("Type a question first.")
    elif not st.session_state.ready:
        st.warning("No sources indexed yet. Click **Process URLs** (or Auto-Ingest).")
    elif not os.getenv("GROQ_API_KEY"):
        st.error("Missing GROQ_API_KEY. Add it to .env, then restart Streamlit.")
    else:
        with st.spinner("Searching sources + generating answer..."):
            answer, sources = answer_question(question.strip(), k=k)

        st.markdown("## Answer")
        st.write(answer)

        st.markdown("## Sources")
        if sources:
            for s in sources:
                st.write(s)
        else:
            st.write("No sources returned.")
