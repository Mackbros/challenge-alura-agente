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

SUGGESTED_QUESTIONS = [
    "¿Qué diferencia hay entre PUE y PPD?",
    "¿Qué es el RESICO y quién puede tributar ahí?",
    "¿Hasta cuándo se presenta la declaración anual?",
    "¿Qué retenciones aplican a servicios profesionales?",
    "¿Qué deducciones personales puedo aplicar?",
    "¿Qué es el REPSE y cuándo lo necesito?",
]

st.set_page_config(page_title="Agente Fiscal SAT", page_icon="🧾", layout="centered")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] { font-family: 'Manrope', sans-serif; }

    .stApp {
        background: radial-gradient(circle at 15% 0%, #1b2840 0%, #0e1420 45%, #0a0e16 100%);
    }

    .hero {
        background: linear-gradient(135deg, #4f7cff 0%, #7b5cff 55%, #b04fff 100%);
        border-radius: 20px;
        padding: 28px 32px;
        margin-bottom: 22px;
        box-shadow: 0 10px 30px rgba(79, 124, 255, 0.25);
    }
    .hero h1 {
        color: #fff; font-size: 1.8rem; font-weight: 800; margin: 0 0 6px 0;
    }
    .hero p {
        color: rgba(255,255,255,0.9); font-size: 0.95rem; margin: 0;
    }

    .chip-label {
        color: #9aa7c7; font-weight: 600; font-size: 0.85rem;
        text-transform: uppercase; letter-spacing: 0.04em;
        margin: 4px 0 10px 2px;
    }

    div[data-testid="stButton"] > button {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 14px;
        color: #e8ecf7;
        padding: 10px 14px;
        font-weight: 600;
        font-size: 0.85rem;
        text-align: left;
        transition: all 0.15s ease;
        width: 100%;
    }
    div[data-testid="stButton"] > button:hover {
        background: linear-gradient(135deg, rgba(79,124,255,0.35), rgba(176,79,255,0.35));
        border-color: rgba(176,79,255,0.5);
        color: #fff;
        transform: translateY(-1px);
    }

    div[data-testid="stChatMessage"] {
        border-radius: 16px;
        padding: 4px 6px;
        margin-bottom: 6px;
    }

    div[data-testid="stChatInput"] textarea {
        border-radius: 14px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h1>🧾 Agente Fiscal SAT</h1>
        <p>Agente RAG que responde dudas fiscales del SAT México a partir de un PDF — Challenge Alura Agente.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if not os.getenv("GROQ_API_KEY"):
    st.error("Falta GROQ_API_KEY. Configúrala en .env o variable de entorno.")
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
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

if not st.session_state.history:
    st.markdown('<div class="chip-label">Preguntas frecuentes</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    for i, q in enumerate(SUGGESTED_QUESTIONS):
        if cols[i % 2].button(q, key=f"chip_{i}"):
            st.session_state.pending_question = q

for q, a in st.session_state.history:
    st.chat_message("user").write(q)
    st.chat_message("assistant").write(a)

pregunta = st.chat_input("Pregunta algo sobre el documento fiscal…")
if not pregunta and st.session_state.pending_question:
    pregunta = st.session_state.pending_question
    st.session_state.pending_question = None

if pregunta:
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
