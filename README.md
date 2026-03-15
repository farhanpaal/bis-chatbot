# 🏛️ BISBot — AI Chatbot for Bureau of Indian Standards

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green?style=for-the-badge&logo=fastapi)
![Groq](https://img.shields.io/badge/Groq-LLaMA--3.3-orange?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)

**An open-source RAG-powered AI chatbot that answers any question about the Bureau of Indian Standards website (bis.gov.in)**

[🚀 Quick Start](#-quick-start) • [📖 Full Setup](#-full-setup-with-crawler) • [🏗️ Architecture](#️-architecture) • [🤝 Contributing](#-contributing)

</div>

---

## ✨ Features

- 🤖 **AI-Powered Answers** — Groq LLaMA-3.3-70B for fast, accurate responses
- 📚 **Full BIS Coverage** — Crawls and indexes 300+ pages from bis.gov.in
- 🔍 **RAG Pipeline** — Retrieval-Augmented Generation with ChromaDB vector search
- 💬 **Conversation Memory** — Full multi-turn context across the session
- 🚫 **Out-of-Scope Detection** — Politely declines non-BIS questions
- 🌐 **English-Only Crawling** — Filters out Hindi content automatically
- 📎 **Source Citations** — Every answer links back to the exact BIS page
- ⚡ **Streaming Responses** — Real-time token-by-token display
- 🎨 **Professional UI** — Dark theme, mobile-responsive, no build step

---

## 📁 Project Structure

```
bis-chatbot/
│
├── 📄 demo_api.py          # ⭐ Start here — works instantly, no crawling needed
├── 📄 api.py               # Full RAG API (requires crawler + ingest first)
├── 📄 crawler.py           # Async English-only BIS website crawler
├── 📄 ingest.py            # Chunking + embedding + ChromaDB vector store
│
├── 📄 requirements.txt     # All Python dependencies
├── 📄 .env.example         # Environment variables template
├── 📄 .gitignore           # Ignores venv, DB, crawled data
├── 📄 start.sh             # One-command full setup (Linux/Mac)
│
└── static/
    └── 📄 index.html       # Single-file chat UI (no build step needed)
```

---

## 🚀 Quick Start

> **Fastest way to run** — uses pre-loaded BIS knowledge, no crawling required. Up in under 5 minutes.

### Step 1 — Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/bis-chatbot.git
cd bis-chatbot
```

### Step 2 — Create a virtual environment

**Windows:**
```bash
python -m venv bisbot-env
bisbot-env\Scripts\activate
```

**Mac/Linux:**
```bash
python -m venv bisbot-env
source bisbot-env/bin/activate
```

You should see `(bisbot-env)` at the start of your terminal prompt.

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

> ⏳ First install takes 3–5 minutes — `sentence-transformers` is a large package, let it finish.

### Step 4 — Get a free Groq API key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up for free
3. Click **API Keys** → **Create API Key**
4. Copy the key (starts with `gsk_`)

### Step 5 — Set your API key

**Windows:**
```bash
set GROQ_API_KEY=gsk_your_key_here
```

**Mac/Linux:**
```bash
export GROQ_API_KEY=gsk_your_key_here
```

Or create a `.env` file in the project root:
```
GROQ_API_KEY=gsk_your_key_here
```

### Step 6 — Run the chatbot

```bash
python demo_api.py
```

Open your browser: **http://localhost:8000** 🎉

---

## 📖 Full Setup (with Crawler)

> For production use — crawls all 300+ BIS pages for comprehensive, accurate answers.

### Step 1–5
Complete the same steps as Quick Start above.

### Step 6 — Crawl the BIS website

```bash
python crawler.py
```

What this does:
- Visits 300+ pages across bis.gov.in
- Automatically skips Hindi/Devanagari content
- Skips PDFs, images, and non-HTML files
- Saves everything to `crawled_data.json`

⏳ Takes approximately **10–20 minutes**

### Step 7 — Build the vector database

```bash
python ingest.py
```

What this does:
- Splits each page into 500-token overlapping chunks
- Converts chunks to vector embeddings using `all-MiniLM-L6-v2` (runs locally, free)
- Stores all vectors in ChromaDB at `./chroma_db/`

⏳ Takes approximately **3–5 minutes**

### Step 8 — Start the full API

```bash
python api.py
```

Open your browser: **http://localhost:8000** 🎉

---

## 📦 What Each Dependency Does

```
aiohttp>=3.9.0               # Async HTTP client — makes the crawler fast
beautifulsoup4>=4.12.0       # Parses HTML to extract clean readable text
chromadb>=0.4.22             # Vector database to store and search embeddings
sentence-transformers>=2.3.0 # Local embedding model (all-MiniLM-L6-v2)
fastapi>=0.109.0             # Web framework for the API server
uvicorn[standard]>=0.27.0    # ASGI server that runs FastAPI
openai>=1.12.0               # OpenAI-compatible SDK — works with Groq too
pydantic>=2.5.0              # Data validation for API request/response models
lxml>=5.1.0                  # Fast HTML parser used by BeautifulSoup
python-dotenv>=1.0.0         # Loads API keys from .env file automatically
```

---

## 🏗️ Architecture

```
User types a question
        │
        ▼
┌───────────────────────────────────────────────────┐
│               FastAPI Backend                      │
│                                                   │
│  1. Check if question is BIS-related              │
│         │                  │                      │
│   Not related          BIS related                │
│         │                  │                      │
│  Polite decline    Search ChromaDB vector DB      │
│                    (cosine similarity search)     │
│                            │                      │
│                     Top 6 relevant                │
│                     BIS content chunks            │
│                            │                      │
│                   Send to Groq LLaMA-3.3-70B      │
│                   with grounding prompt           │
│                            │                      │
│              Stream answer token by token         │
│              + attach source URLs                 │
└───────────────────────────────────────────────────┘
        │
        ▼
Chat UI renders markdown + clickable source links
```

**RAG Pipeline Stages:**

| Stage | Tool | What happens |
|-------|------|--------------|
| **Crawl** | aiohttp + BeautifulSoup | Visits every BIS page, extracts English text |
| **Chunk** | Custom splitter | Splits into 500-word pieces with 100-word overlap |
| **Embed** | all-MiniLM-L6-v2 | Converts text to 384-dimension vectors (runs locally) |
| **Store** | ChromaDB | Saves vectors + metadata (URL, title, timestamp) |
| **Retrieve** | ChromaDB query | Finds top 6 most relevant chunks for any question |
| **Answer** | Groq LLaMA-3.3-70B | Generates grounded answer, streamed to browser |

---

## 🌐 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Opens the chat UI |
| `POST` | `/api/chat` | Send a message, receive streamed response |
| `GET` | `/api/status` | Server health + indexed chunk count |
| `GET` | `/api/suggestions` | Returns suggested starter questions |
| `GET` | `/api/conversations/{id}` | Get full conversation history |
| `DELETE` | `/api/conversations/{id}` | Clear a conversation |

**Example chat request:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is BIS?", "conversation_id": null}'
```

---

## 🚢 Deploy Online

### Railway (Recommended)

1. Push your code to GitHub
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub**
3. Select your repo
4. Add environment variable: `GROQ_API_KEY` = `gsk_...`
5. Railway auto-deploys — done!

### Render

1. Go to [render.com](https://render.com) → **New Web Service**
2. Connect your GitHub repo
3. Set **Build Command**: `pip install -r requirements.txt`
4. Set **Start Command**: `uvicorn demo_api:app --host 0.0.0.0 --port $PORT`
5. Add environment variable: `GROQ_API_KEY` = `gsk_...`
6. Click Deploy

---

## ❓ Troubleshooting

**`(bisbot-env)` not showing in terminal**
Your venv isn't activated. Run the activate command again:
```bash
bisbot-env\Scripts\activate    # Windows
source bisbot-env/bin/activate  # Mac/Linux
```

**`No such file or directory: demo-api.py`**
Use underscore not hyphen:
```bash
python demo_api.py   ✅
python demo-api.py   ❌
```

**`ModuleNotFoundError`**
Dependencies not installed, or wrong Python. Make sure venv is active then:
```bash
pip install -r requirements.txt
```

**API key errors**
Check your key is set:
```bash
echo %GROQ_API_KEY%   # Windows
echo $GROQ_API_KEY    # Mac/Linux
```

**Slow first startup (~30 seconds)**
Normal — `sentence-transformers` downloads the embedding model on first run (~90MB). Only happens once.

**Port 8000 already in use**
```bash
uvicorn demo_api:app --port 8001
```
Then open http://localhost:8001

---

## 🤝 Contributing

Contributions welcome! Here's how:

1. Fork the repository
2. Create a branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Commit: `git commit -m "Add your feature"`
5. Push: `git push origin feature/your-feature`
6. Open a Pull Request

**Ideas for contributions:**
- Add PDF crawling support
- Add Hindi language query support
- Improve relevance scoring with hybrid search
- Add a feedback/thumbs up-down system
- Add more pre-loaded BIS topics to `demo_api.py`

---

## 📄 License

MIT License — free to use, modify, and distribute. See `LICENSE` file.

---

## 🙏 Acknowledgements

- Built for **FOSS × BIS Hackathon 2026**
- Data: [bis.gov.in](https://www.bis.gov.in) — Bureau of Indian Standards
- LLM: [Groq](https://groq.com) — LLaMA-3.3-70B (free tier available)
- Embeddings: [sentence-transformers](https://www.sbert.net/) — all-MiniLM-L6-v2
- Vector DB: [ChromaDB](https://www.trychroma.com/)
- UI: Vanilla JS + Google Fonts (no build step, no npm)

---

<div align="center">
Made with ❤️ for open source · <a href="https://bis.gov.in">bis.gov.in</a>
</div>