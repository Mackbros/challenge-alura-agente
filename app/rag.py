"""Núcleo RAG: carga PDF, indexa en FAISS y responde preguntas con Groq."""
from __future__ import annotations

import os
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate

INDEX_DIR = Path(__file__).resolve().parent.parent / "data" / "faiss_index"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

SYSTEM_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template=(
        "Eres un asistente fiscal experto en el SAT de México. "
        "Responde ÚNICAMENTE con la información del contexto. "
        "Si el contexto no contiene la respuesta, di que no está en el documento. "
        "Sé claro y cita el concepto fiscal cuando aplique.\n\n"
        "Contexto:\n{context}\n\n"
        "Pregunta: {question}\n\n"
        "Respuesta:"
    ),
)


def _embeddings() -> HuggingFaceEmbeddings:
    """Embeddings locales gratis (sin API key)."""
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)


def build_index(pdf_path: str) -> FAISS:
    """Lee el PDF, lo trocea y construye el índice vectorial FAISS."""
    docs = PyPDFLoader(pdf_path).load()
    chunks = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=150
    ).split_documents(docs)
    store = FAISS.from_documents(chunks, _embeddings())
    INDEX_DIR.parent.mkdir(parents=True, exist_ok=True)
    store.save_local(str(INDEX_DIR))
    return store


def load_index() -> FAISS | None:
    """Carga el índice ya construido, o None si no existe."""
    if not INDEX_DIR.exists():
        return None
    return FAISS.load_local(
        str(INDEX_DIR),
        _embeddings(),
        allow_dangerous_deserialization=True,
    )


def make_chain(store: FAISS) -> ConversationalRetrievalChain:
    """Arma la cadena RAG conversacional sobre el índice dado."""
    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=store.as_retriever(search_kwargs={"k": 4}),
        combine_docs_chain_kwargs={"prompt": SYSTEM_PROMPT},
        return_source_documents=True,
    )
