# 🚀 Deploy to Hugging Face Spaces - Simple Guide

Your project is ready to deploy! Follow these steps:

## Step 1: Create a Hugging Face Account
If you don't have one: https://huggingface.co/join

## Step 2: Create a New Space
1. Go to https://huggingface.co/spaces
2. Click **"Create new Space"** (blue button)
3. Fill in:
   - **Owner**: Your username
   - **Space name**: `verite-assistant` (or any name you like)
   - **License**: Apache 2.0
   - **Select the Space SDK**: Choose **Streamlit**
   - **Space hardware**: CPU basic (free)
   - **Visibility**: Public
4. Click **"Create Space"**

## Step 3: Upload Your Files

### Option A: Git Push (Recommended)
```bash
# Initialize git if not done
git init
git add .
git commit -m "Initial commit"

# Add your HF Space as remote
# Replace YOUR_USERNAME and verite-assistant with your actual values
git remote add space https://huggingface.co/spaces/YOUR_USERNAME/verite-assistant

# Swap README files
git mv README.md GITHUB_README.md
git mv HF_README.md README.md
git add .
git commit -m "Prepare for deployment"

# Push to HF Space
git push space main
```

### Option B: Web Upload (Easier for beginners)
1. In your Space page, click **"Files"** tab
2. Click **"Add file"** → **"Upload files"**
3. Upload these files/folders:
   - ✅ `app.py`
   - ✅ `agent.py`
   - ✅ `config.py`
   - ✅ `memory.py`
   - ✅ `prompts.py`
   - ✅ `vector_store.py`
   - ✅ `ingest.py`
   - ✅ `requirements.txt`
   - ✅ `logo.jpg`
   - ✅ `chroma_db/` (entire folder - IMPORTANT!)
   - ✅ `memory.db`
   - ❌ **DO NOT upload**: `data/` folder, `.env` file, `logs/`
4. Rename `HF_README.md` to `README.md` (delete old README.md first)
5. Click **"Commit changes to main"**

## Step 4: Add Your API Key
1. In your Space, click **"Settings"** (top right)
2. Scroll to **"Repository secrets"**
3. Click **"Add a secret"**
4. Enter:
   - **Name**: `GROQ_API_KEY`
   - **Value**: Your Groq API key (get it from https://console.groq.com/keys)
5. Click **"Save"**

## Step 5: Wait for Build
- The Space will automatically build (takes 2-3 minutes)
- Watch the **"Logs"** tab to see progress
- When done, you'll see "Running" status and the app will appear!

## Step 6: Share Your Chatbot! 🎉
Your chatbot is now live at:
```
https://huggingface.co/spaces/YOUR_USERNAME/verite-assistant
```

Anyone can use it without installing anything or needing an API key!

---

## Troubleshooting

### "GROQ_API_KEY is not set"
→ Go to Settings → Repository secrets → Add `GROQ_API_KEY`

### "Knowledge base is empty"
→ Make sure you uploaded the entire `chroma_db/` folder with all its contents

### Build fails
→ Check the Logs tab for error messages
→ Verify `requirements.txt` was uploaded

### App is slow
→ Free tier CPU is limited. Consider upgrading to CPU upgrade ($0.03/hour) in Settings

---

## Get a Free Groq API Key

1. Go to https://console.groq.com
2. Sign up (free)
3. Go to https://console.groq.com/keys
4. Click **"Create API Key"**
5. Copy the key (starts with `gsk_...`)
6. Add it to your HF Space secrets

Groq is FREE and very fast! 🚀

---

## Need Help?

- Hugging Face Docs: https://huggingface.co/docs/hub/spaces
- Streamlit Docs: https://docs.streamlit.io
- Groq Docs: https://console.groq.com/docs
