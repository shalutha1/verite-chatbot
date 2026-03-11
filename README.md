---
title: Veri - Verité Research Assistant
emoji: 📚
colorFrom: blue
colorTo: indigo
sdk: streamlit
sdk_version: "1.38.0"
app_file: app.py
pinned: false
---

# Veri — Verité Research Assistant

An AI chatbot for exploring Verité Research publications on Sri Lanka's economy, governance, and policy.

## 🔗 Live App
**[https://huggingface.co/spaces/shaluthaperera/veri-chatbot](https://huggingface.co/spaces/shaluthaperera/veri-chatbot)**

---

## Submission Files
- 📄 **[publications.md](./publications.md)** — The 5 Verité Research publications used (title, year, URL)
- 💬 **[sample_qa.md](./sample_qa.md)** — 5 sample questions and answers from the chatbot
- 🧠 **[PROMPTS.md](./PROMPTS.md)** — System prompt design decisions

---

## Features
- 🤖 Smart routing — searches knowledge base only when needed
- 🔍 Hybrid search — vector + keyword search with RRF fusion
- 📄 Citations — shows source document and page numbers
- 💬 Natural conversation — handles greetings and follow-ups
- 🧠 Long-term memory — remembers conversations across sessions

---

## How to Run Locally

### 1. Clone the repo
```bash
git clone https://github.com/shalutha1/verite-chatbot.git
cd verite-chatbot
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment variables
```bash
cp env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 4. Run the app
```bash
python -m streamlit run app.py
```

> **Note:** The `chroma_db/` folder (pre-built knowledge base) is included in the repo. You do **not** need to run `ingest.py` unless you want to rebuild from scratch.

---

## How to Use
Just ask questions about Verité Research's publications:
- "What does Verité say about property taxes?"
- "Explain governance-linked bonds"
- "What are the findings on trade facilitation?"

---

## Tech Stack
| Component | Technology |
|---|---|
| LLM | Groq (Llama 3.3 70B) |
| Vector DB | ChromaDB |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Keyword Search | BM25 (rank-bm25) |
| Search Fusion | Reciprocal Rank Fusion (RRF) |
| Memory | SQLite (long-term across sessions) |
| UI | Streamlit |
| Deployment | HuggingFace Spaces |

---

**Note**: This chatbot only answers questions based on Verité Research's publications. It does not have general knowledge outside of those documents.
