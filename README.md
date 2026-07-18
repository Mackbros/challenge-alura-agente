# 🧾 Agente Fiscal SAT — Challenge Alura Agente

Agente de IA que responde preguntas fiscales (SAT México) basándose en el contenido de un
documento PDF, usando **RAG** (Retrieval-Augmented Generation). Proyecto del *Challenge Alura
Agente* — ONE / Alura LATAM.

## Descripción general

El usuario sube (o el repo ya incluye) una guía fiscal en PDF. El agente la trocea, la indexa
en un vector store y responde preguntas en lenguaje natural citando las páginas fuente. Si la
respuesta no está en el documento, lo dice — no inventa.

## Arquitectura

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  PDF fiscal  │ ──▶ │  Splitter +      │ ──▶ │  FAISS index    │
│  (data/)     │     │  Embeddings      │     │  (vector store) │
└──────────────┘     │  MiniLM-L6-v2    │     └────────┬────────┘
                     └──────────────────┘              │
                                                       ▼
┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Usuario     │ ──▶ │  Streamlit UI    │ ──▶ │  Retriever k=4  │
│  (pregunta)  │     │  (chat)          │     └────────┬────────┘
└──────────────┘     └──────────────────┘              │
        ▲                                               ▼
        │            ┌──────────────────┐     ┌─────────────────┐
        └─────────── │  Respuesta +     │ ◀── │  Llama 3.1 8B   │
                     │  páginas fuente  │     │  (Groq, LLM)    │
                     └──────────────────┘     └─────────────────┘
```

Flujo RAG: `PyPDFLoader` → `RecursiveCharacterTextSplitter` → `HuggingFaceEmbeddings`
(local, sin costo) → `FAISS` → `ConversationalRetrievalChain` (recupera k=4 chunks) →
`ChatGroq` (Llama 3.1 8B, gratis) → respuesta con fuentes.

## Tecnologías

| Componente     | Herramienta                                  |
|----------------|-----------------------------------------------|
| UI             | Streamlit                                    |
| Orquestación   | LangChain                                    |
| LLM            | Groq — `llama-3.1-8b-instant` (gratis)       |
| Embeddings     | HuggingFace `all-MiniLM-L6-v2` (local, gratis)|
| Vector store   | FAISS (local)                                |
| Lectura PDF    | pypdf                                         |
| Deploy         | Docker sobre Oracle Cloud (OCI)              |

## Cómo ejecutar (local)

```bash
git clone <tu-repo>
cd challenge-alura-agente

python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env          # pon tu GROQ_API_KEY (gratis en console.groq.com)
# coloca tu PDF en data/guia_fiscal_sat.pdf

streamlit run app/main.py
```

Abre http://localhost:8501

> **Obtener API key gratis:** crea cuenta en [console.groq.com](https://console.groq.com/keys),
> genera una key (`gsk_...`), sin tarjeta de crédito.

### Con Docker

```bash
docker build -t agente-fiscal .
docker run -p 8501:8501 -e GROQ_API_KEY=gsk_... agente-fiscal
```

## Ejemplos de preguntas

- ¿Cuándo se causa el IVA en flujo de efectivo?
- ¿Qué diferencia hay entre un CFDI PUE y uno PPD?
- ¿Qué es un complemento de pago (REP) y cuándo se emite?
- ¿Qué retenciones aplican a servicios profesionales?
- ¿Cuál es la fecha límite para timbrar la nómina?

## Ejemplos de respuestas

> **P:** ¿Qué diferencia hay entre un CFDI PUE y uno PPD?
>
> **R:** Según el documento, un CFDI con método de pago **PUE** (Pago en Una sola Exhibición)
> se emite cuando la operación se paga por completo al momento de facturar. Un **PPD** (Pago
> en Parcialidades o Diferido) se usa cuando el pago ocurre después; este último requiere emitir
> un complemento de pago (REP) por cada abono recibido. *(Fuentes: páginas 4, 5)*

## Despliegue en OCI

Ver [docs/DEPLOY_OCI.md](docs/DEPLOY_OCI.md).

**App en vivo:** _<pega aquí la URL pública tras el deploy>_
