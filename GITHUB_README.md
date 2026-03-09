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

## Features
- 🤖 Smart routing — searches knowledge base only when needed
- 🔍 Hybrid search — vector + keyword search with RRF fusion
- 📄 Citations — shows source document and page numbers
- 💬 Natural conversation — handles greetings and follow-ups

## How to Use
Just ask questions about Verité Research's publications:
- "What does Verité say about property taxes?"
- "Explain governance-linked bonds"
- "What are the findings on trade facilitation?"

## Tech Stack
- **LLM**: Groq (Llama 3.3 70B)
- **Vector DB**: ChromaDB
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **UI**: Streamlit
- **Memory**: SQLite

---

**Note**: This chatbot only answers questions based on Verité Research's publications. It does not have general knowledge.
