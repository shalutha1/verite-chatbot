# Hugging Face Spaces Deployment Guide

## Quick Deploy Steps

### 1. Initialize Git (if not already done)
```bash
git init
git add .
git commit -m "Initial commit with pre-built vector store"
```

### 2. Create Hugging Face Space
1. Go to https://huggingface.co/spaces
2. Click **"Create new Space"**
3. Fill in:
   - **Space name**: `verite-assistant` (or your choice)
   - **License**: Apache 2.0
   - **SDK**: Streamlit
   - **Visibility**: Public
4. Click **"Create Space"**

### 3. Link and Push to HF Space
```bash
# Add HF Space as remote (replace YOUR_USERNAME and SPACE_NAME)
git remote add space https://huggingface.co/spaces/YOUR_USERNAME/SPACE_NAME

# Rename HF_README.md to README.md for the Space
git mv README.md GITHUB_README.md
git mv HF_README.md README.md
git add .
git commit -m "Prepare for HF Spaces deployment"

# Push to HF Space
git push space main
```

### 4. Add API Key Secret
1. Go to your Space page on Hugging Face
2. Click **Settings** → **Repository secrets**
3. Add secret:
   - **Name**: `GROQ_API_KEY`
   - **Value**: Your Groq API key (starts with `gsk_...`)
4. Click **Save**

### 5. Wait for Build
Your Space will automatically build and deploy. You'll get a URL like:
```
https://huggingface.co/spaces/YOUR_USERNAME/verite-assistant
```

## Important Notes

✅ **Vector database (`chroma_db/`) is already built** — no need to run ingest.py on HF Spaces

✅ **PDFs are NOT uploaded** — they stay in your local `data/` folder only

✅ **Memory database (`memory.db`) is included** — starts empty, gets populated as users chat

⚠️ **Never commit your `.env` file** — it's already in `.gitignore`

## Troubleshooting

### If build fails:
- Check that `requirements.txt` has all dependencies
- Verify `GROQ_API_KEY` is set in Secrets
- Check Space logs for errors

### If app shows "Knowledge base empty":
- Ensure `chroma_db/` folder was pushed with all files
- Check that `.gitignore` doesn't exclude `chroma_db/`

### To update the knowledge base:
1. Add new PDFs to local `data/` folder
2. Run `python ingest.py --reset`
3. Commit and push updated `chroma_db/`:
   ```bash
   git add chroma_db/
   git commit -m "Update knowledge base"
   git push space main
   ```

## Alternative: Direct HF Git Push

If you prefer to work directly with HF's repo:

```bash
# Clone the Space repo
git clone https://huggingface.co/spaces/YOUR_USERNAME/SPACE_NAME
cd SPACE_NAME

# Copy your files (excluding data/)
cp -r ../assigmnet/* .
rm -rf data/  # Don't copy PDFs

# Rename README
mv README.md GITHUB_README.md
mv HF_README.md README.md

# Commit and push
git add .
git commit -m "Deploy Veri chatbot"
git push
```

## Sharing with Others

Once deployed, anyone can access your chatbot at:
```
https://huggingface.co/spaces/YOUR_USERNAME/SPACE_NAME
```

No installation or API keys needed for users! 🎉
