"""UI Streamlit del agente fiscal RAG."""
from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from rag import build_index, load_index, make_chain

load_dotenv()

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_PDF = DATA_DIR / "guia_fiscal_sat.pdf"

st.set_page_config(page_title="Agente Fiscal SAT", page_icon="🧾")
st.title("🧾 Agente Fiscal SAT")
st.caption("Agente RAG que responde dudas fiscales desde un PDF. Challenge Alura Agente.")

if not os.getenv("OPENAI_API_KEY"):
    st.error("Falta OPENAI_API_KEY. Configúrala en .env o variable de entorno.")
    st.stop()


@st.cache_resource(show_spinner="Indexando documento…")
def get_chain():
    store = load_index()
    if store is None:
        if not DEFAULT_PDF.exists():
            return None
        store = build_index(str(DEFAULT_PDF))
    return make_chain(store)


chain = get_chain()
if chain is None:
    st.warning(f"Sube el PDF fuente en: {DEFAULT_PDF}")
    st.stop()

if "history" not in st.session_state:
    st.session_state.history = []

for q, a in st.session_state.history:
    st.chat_message("user").write(q)
    st.chat_message("assistant").write(a)

if pregunta := st.chat_input("Pregunta algo sobre el documento fiscal…"):
    st.chat_message("user").write(pregunta)
    with st.chat_message("assistant"):
        with st.spinner("Pensando…"):
            res = chain.invoke(
                {"question": pregunta, "chat_history": st.session_state.history}
            )
            answer = res["answer"]
            st.write(answer)
            srcs = {d.metadata.get("page", "?") for d in res.get("source_documents", [])}
            if srcs:
                st.caption("Fuentes (páginas): " + ", ".join(str(s) for s in sorted(srcs)))
    st.session_state.history.append((pregunta, answer))
