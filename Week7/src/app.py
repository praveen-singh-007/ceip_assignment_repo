"""
app.py
------------------------------------------------------------------
Streamlit front-end for the RAG Document QA system.

Run with:
    cd src
    streamlit run app.py
------------------------------------------------------------------
"""

import os
import time
import streamlit as st
from dotenv import load_dotenv

from vectorstore import VectorStore
from chatbot import Chatbot

load_dotenv()
st.set_page_config(page_title="Document QA Bot", page_icon="📄", layout="wide")


def main():
    st.title("📄 Document QA Bot (RAG, powered by Groq)")
    st.caption(
        "Retrieval-Augmented Generation system — ask questions about your own "
        "PDFs and get answers grounded in the document's actual content."
    )

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "vectorstore" not in st.session_state:
        st.session_state.vectorstore = None
    if "chatbot" not in st.session_state:
        st.session_state.chatbot = None

    # ------------------------------------------------------------------ #
    # SIDEBAR — configuration
    # ------------------------------------------------------------------ #
    with st.sidebar:
        st.header("🔑 Configuration")
        groq_api_key = st.text_input(
            "Groq API Key",
            type="password",
            value=os.environ.get("GROQ_API_KEY", ""),
            help="Get a free key at https://console.groq.com/keys",
        )
        model = st.selectbox(
            "Groq model",
            ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "gemma2-9b-it"],
            index=0,
        )

        st.divider()
        st.header("⚙️ Chunking & Retrieval")
        chunk_size = st.slider("Chunk size (chars)", 300, 1500, 800, 50)
        chunk_overlap = st.slider("Chunk overlap (chars)", 0, 400, 150, 25)
        top_k = st.slider("Chunks retrieved (top-k)", 1, 10, 4)
        search_mode = st.radio("Search mode", ["hybrid", "vector", "keyword"], index=0)
        use_reranker = st.checkbox("Use cross-encoder re-ranking", value=False)

        st.divider()
        uploaded_file = st.file_uploader("Upload a PDF or .txt file", type=["pdf", "txt"])
        build_clicked = st.button("🔨 Build / Rebuild Index", use_container_width=True)

    # ------------------------------------------------------------------ #
    # BUILD INDEX
    # ------------------------------------------------------------------ #
    if build_clicked:
        if not uploaded_file:
            st.sidebar.error("Please upload a document first.")
        else:
            with st.spinner("Ingesting document, creating embeddings, building index..."):
                tmp_path = f"_uploaded_{uploaded_file.name}"
                with open(tmp_path, "wb") as f:
                    f.write(uploaded_file.read())

                vs = VectorStore(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
                start = time.time()
                vs.build_all(tmp_path)
                elapsed = time.time() - start

                st.session_state.vectorstore = vs
                st.session_state.chatbot = None  # rebuild on next query
                st.session_state.last_build_stats = {
                    "chunks": len(vs.chunks),
                    "dim": vs.embedding_dim,
                    "seconds": round(elapsed, 2),
                }
            st.sidebar.success(
                f"Indexed {len(vs.chunks)} chunks "
                f"({vs.embedding_dim}-dim embeddings) in {elapsed:.1f}s"
            )

    if "last_build_stats" in st.session_state:
        s = st.session_state.last_build_stats
        st.sidebar.info(f"📊 {s['chunks']} chunks · {s['dim']}-dim vectors · built in {s['seconds']}s")

    # ------------------------------------------------------------------ #
    # CHAT
    # ------------------------------------------------------------------ #
    if st.session_state.vectorstore is None:
        st.info("👈 Upload a document and click **Build / Rebuild Index** to get started.")
        return

    if not groq_api_key:
        st.warning("Enter your Groq API key in the sidebar to start chatting.")
        return

    if st.session_state.chatbot is None:
        st.session_state.chatbot = Chatbot(
            vectorstore=st.session_state.vectorstore,
            groq_api_key=groq_api_key,
            model=model,
            top_k=top_k,
            search_mode=search_mode,
            use_reranker=use_reranker,
        )

    for turn in st.session_state.chat_history:
        with st.chat_message(turn["role"]):
            st.write(turn["content"])
            if turn["role"] == "assistant" and turn.get("sources"):
                with st.expander("📚 Retrieved sources"):
                    for s in turn["sources"]:
                        st.markdown(f"**p.{s['page']} · score {s['score']:.3f}**\n\n> {s['text'][:300]}...")

    user_query = st.chat_input("Ask a question about the document...")
    if user_query:
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.write(user_query)

        with st.chat_message("assistant"):
            with st.spinner("Retrieving context and generating answer..."):
                answer, sources = st.session_state.chatbot.respond(user_query)
            st.write(answer)
            with st.expander("📚 Retrieved sources"):
                for s in sources:
                    st.markdown(f"**p.{s['page']} · score {s['score']:.3f}**\n\n> {s['text'][:300]}...")

        st.session_state.chat_history.append(
            {"role": "assistant", "content": answer, "sources": sources}
        )


if __name__ == "__main__":
    main()
