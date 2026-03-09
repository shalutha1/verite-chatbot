# 🚀 Quick Deployment Checklist

## ✅ Pre-Deployment (Done!)
- [x] Vector database built (`chroma_db/` exists with 3.7MB)
- [x] `.gitignore` updated (excludes `data/` but includes `chroma_db/`)
- [x] `.gitattributes` created (for large files)
- [x] `HF_README.md` ready (has Streamlit frontmatter)

## 📋 Deploy to Hugging Face Spaces

### Step 1: Create Space on Hugging Face
1. Go to https://huggingface.co/spaces
2. Click **"Create new Space"**
3. Settings:
   - Name: `verite-assistant` (or your choice)
   - SDK: **Streamlit**
   - Visibility: **Public**
4. Click **"Create Space"**

### Step 2: Push Your Code

**Option A: Using Git (Recommended)**
```bash
# In your project folder
git init
git add .
git commit -m "Initial commit"

# Add HF Space as remote (replace YOUR_USERNAME and SPACE_NAME)
git remote add space https://huggingface.co/spaces/YOUR_USERNAME/SPACE_NAME

# Rename README for HF Spaces
git mv README.md GITHUB_README.md
git mv HF_README.md README.md
git add .
git commit -m "Prepare for HF deployment"

# Push
git push space main
```

**Option B: Upload via Web Interface**
1. Go to your Space → **Files**
2. Click **"Add file"** → **"Upload files"**
3. Upload ALL files EXCEPT:
   - `data/` folder (PDFs)
   - `.env` file
   - `logs/` folder
4. Rename `HF_README.md` to `README.md` after upload

### Step 3: Add API Key Secret
1. In your Space, go to **Settings** → **Repository secrets**
2. Click **"Add a secret"**
3. Add:
   - Name: `GROQ_API_KEY`
   - Value: `gsk_...` (your Groq API key)
4. Click **Save**

### Step 4: Wait for Build
- Space will automatically build (takes 2-3 minutes)
- Check **Logs** tab if there are errors
- Once ready, you'll see the app running!

## 🎉 Done!

Your chatbot will be live at:
```
https://huggingface.co/spaces/YOUR_USERNAME/SPACE_NAME
```

Share this URL with anyone — they can use it without any setup!

## 🔧 Common Issues

**"Knowledge base empty"**
→ Make sure `chroma_db/` folder was uploaded with all files

**"GROQ_API_KEY not set"**
→ Add it in Settings → Repository secrets

**Build fails**
→ Check Logs tab for errors
→ Verify `requirements.txt` is correct

## 📝 Notes

- PDFs stay on your local machine only
- Vector database is pre-built and included
- Users don't need API keys
- Memory is per-session (resets on refresh)
