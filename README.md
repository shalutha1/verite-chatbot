# Veri — Verité Research Assistant

An agentic RAG chatbot for Verité Research publications.  
Built with Anthropic Claude, ChromaDB, sentence-transformers, and Streamlit.

**Live demo:** [your-huggingface-space-url-here]

---

## Features

- 🤖 **Smart routing** — only searches the knowledge base when genuinely needed
- 🔍 **Hybrid search** — vector similarity + BM25 keyword search fused via Reciprocal Rank Fusion
- 📄 **Citations** — source document and page number shown for every retrieved answer
- 🧠 **Long-term memory** — remembers previous sessions via SQLite
- 💬 **Natural conversation** — responds to greetings and small talk without unnecessary retrieval

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/verite-chatbot.git
cd verite-chatbot
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Set environment variables

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 4. Add PDFs

Place your 5 Verité Research PDFs in the `data/` folder.  
*(PDFs are excluded from the repo — see .gitignore)*

### 5. Run ingestion

```bash
python ingest.py
```

To wipe and re-ingest:
```bash
python ingest.py --reset
```

### 6. Run the app

```bash
streamlit run app.py
```

---

## Deployment (Hugging Face Spaces)

> **Key principle:** PDFs are never committed. Instead, run ingestion locally first,
> then commit the pre-built `chroma_db/` so the deployed app works without any PDFs.

### Step 1 — Build the knowledge base locally

```bash
# Place your 5 PDFs in data/ then run:
python ingest.py
```

This creates `chroma_db/` with all embeddings.

### Step 2 — Commit the pre-built vector store

```bash
git add chroma_db/
git add memory.db        # empty DB is fine — gets populated at runtime
git commit -m "Add pre-built vector store"
git push
```

### Step 3 — Create a Hugging Face Space

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces) → **New Space**
2. Name it (e.g. `verite-assistant`)
3. SDK: **Streamlit**
4. Visibility: **Public**
5. Link to your GitHub repo (or push directly to the HF repo)

### Step 4 — Rename HF_README.md → README.md on the Space

HuggingFace Spaces requires the frontmatter (title, sdk, app_file) in the
root `README.md`. When pushing to the HF repo specifically, use `HF_README.md`
as your `README.md`. Your GitHub repo keeps its own `README.md`.

### Step 5 — Add your API key as a Secret

In your Space → **Settings → Repository Secrets**:

```
ANTHROPIC_API_KEY = sk-ant-...
```

**Never put your API key in any file that gets committed.**

### Step 6 — Deploy

Push to the Space repo. It builds automatically and gives you a public URL like:  
`https://huggingface.co/spaces/yourusername/verite-assistant`

---

## Project Structure

```
verite-chatbot/
├── app.py              # Streamlit UI
├── agent.py            # Core agent with Claude tool use
├── vector_store.py     # ChromaDB + BM25 hybrid search
├── memory.py           # SQLite long-term memory
├── ingest.py           # PDF ingestion pipeline
├── prompts.py          # System prompt and tool definitions
├── config.py           # Central configuration
├── chroma_db/          # Persisted vector DB (committed to repo)
├── memory.db           # SQLite memory DB (committed to repo)
├── data/               # PDFs go here (NOT committed)
├── PROMPTS.md          # Prompt design decisions
├── publications.md     # List of 5 Verité PDFs used
├── sample_qa.md        # 5 sample questions and answers
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ | Your Anthropic API key |
| `CLAUDE_MODEL` | ❌ | Override model (default: `claude-3-5-sonnet-20241022`) |

---

## Publications Used

See [publications.md](publications.md)

## Sample Q&A

See [sample_qa.md](sample_qa.md)
