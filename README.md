# 🏛️ BISBot — AI Assistant for Bureau of Indian Standards

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green?style=for-the-badge&logo=fastapi)
![Groq](https://img.shields.io/badge/Groq-LLaMA--3.3--70B-orange?style=for-the-badge)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20DB-purple?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-gray?style=for-the-badge)

**An open-source AI chatbot that answers any question about the Bureau of Indian Standards (bis.gov.in) — with grounded answers, source citations, and conversation memory.**

Built for the **FOSS × BIS Hackathon 2026**

</div>

---
<img src="../bis-chatbot/static/UI.PNG">

## 📸 What It Looks Like

```
┌──────────────────────────────────────────────────────────────┐
│  🛡 BISBot          Bureau of Indian Standards · bis.gov.in  │
│                                          ● Online  + ⎘ ✕    │
├─────────────────┬────────────────────────────────────────────┤
│  New Convo      │                                            │
│                 │       🛡                                   │
│  Quick Q's      │    Ask me anything about BIS               │
│  ─────────────  │    AI assistant powered by the complete    │
│  What is BIS?   │    Bureau of Indian Standards website.     │
│  ISI Mark?      │                                            │
│  Lab services   │    [What is BIS?] [ISI Mark?] [Labs]      │
│  Hallmarking    │    [Consumer awareness] [Latest updates]  │
│                 │                                            │
│  Session Info   ├────────────────────────────────────────────│
│  ID:  a3f9b2…  │  ┌──────────────────────────────────────┐  │
│  Msgs: 4        │  │ Ask about certifications, schemes…   │  │
│  Model: LLaMA   │  └──────────────────────────────────────┘  │
│  Source: bis.…  │   0/2000  Enter to send · Shift+Enter ↵   │
└─────────────────┴────────────────────────────────────────────┘
```

---

## ✨ Features

### 🤖 AI-Powered Answers
Ask any question about BIS in plain English. BISBot retrieves relevant content from the indexed BIS website and generates a clear, accurate answer using the **Groq LLaMA-3.3-70B** model.

### 📎 Source Citations
Every answer includes clickable links back to the exact BIS page the information came from. No guessing — you can verify every claim.

### 💬 Conversation Memory
BISBot remembers what you said earlier in the same session. Ask follow-up questions naturally:
> *"What schemes does BIS offer?"*
> *"Tell me more about the third one."* ← BISBot understands the context

### 🚫 Out-of-Scope Detection
BISBot only answers BIS-related questions. If you ask about stock prices, cricket scores, or anything unrelated, it politely declines and suggests a relevant BIS topic instead.

### 🌐 English-Only Content
The crawler automatically filters out Hindi/Devanagari content and indexes only English text from the BIS website — ensuring clean, readable answers.

### ⚡ Real-Time Streaming
Responses stream token-by-token as they're generated — no waiting for the full answer before you can start reading.

### 📋 Copy Any Response
Every bot response has a **Copy** button. Click it to copy the full answer to your clipboard. You can also copy the entire conversation from the header.

### 📰 Latest BIS Updates
Press releases and news pages are crawled and indexed with timestamps, so BISBot can surface the most recent BIS announcements.

### 🎨 Clean Professional UI
White-themed, mobile-responsive interface with a sidebar for quick questions, session info, and conversation management.

---

## 📁 Project Structure

This is exactly what your folder looks like after cloning and setting up:

```
bis-chatbot/
│
├── 📁 bisbot-env/          ← Virtual environment (created by you, not committed to git)
├── 📁 chroma_db/           ← Vector database (auto-created after running ingest.py)
│
├── 📁 static/
│   ├── 📄 index.html       ← Main chat UI
│   ├── 📄 bis.html         ← Alternate UI
│   ├── 🖼️ logo.png         ← BISBot logo
│   └── 🖼️ standard-img.PNG ← Standard image asset
│
├── 📄 api.py               ← Full production API (needs crawler + ingest first)
├── 📄 crawler.py           ← Async English-only BIS website crawler
├── 📄 demo_api.py          ← ⭐ Start here — instant demo, no crawling needed
├── 📄 ingest.py            ← Chunk → embed → store in ChromaDB
│
├── 📄 requirements.txt     ← All Python dependencies
├── 📄 README.md            ← This file
├── 📄 .env.example         ← Copy this to .env and add your API key
├── 📄 .gitignore           ← Keeps venv and DB out of git
└── 📄 start.sh             ← One-command setup for Linux/Mac
```

> `bisbot-env/` and `chroma_db/` are listed in `.gitignore` — they won't be pushed to GitHub. Anyone who clones the repo creates their own `bisbot-env` locally.

---

## 🚀 Getting Started

### What you need before starting

- **Python 3.10 or newer** — check with `python --version`
- **A free Groq API key** — get one at [console.groq.com](https://console.groq.com) (no credit card needed)
- **Git** — to clone the repo

---

### Option A — Quick Demo (ready in 5 minutes)

Uses pre-loaded BIS knowledge. No crawling needed. Perfect for trying it out.

#### Step 1 · Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/bis-chatbot.git
cd bis-chatbot
```

#### Step 2 · Create a virtual environment

> **Why a virtual environment?**
> A virtual environment keeps this project's packages completely isolated from the rest of your system. Without it, installing packages globally can break other Python projects — or the system itself on some Linux distros. It also ensures anyone who clones this repo gets the exact same package versions.
>
> We name ours `bisbot-env` — you'll see this folder appear in your project directory after running the command below.

**Windows:**
```bash
python -m venv bisbot-env
bisbot-env\Scripts\activate
```

**Mac / Linux:**
```bash
python -m venv bisbot-env
source bisbot-env/bin/activate
```

You'll know it worked when your terminal prompt changes to show `(bisbot-env)` at the start:

```
(bisbot-env) C:\Users\you\bis-chatbot>
```

> **Every time you open a new terminal**, run the activate command again before running any Python files.
> To leave the venv, type `deactivate`.

#### Step 3 · Install dependencies

```bash
pip install -r requirements.txt
```

> ⏳ This takes 3–5 minutes on first run — `sentence-transformers` downloads a ~90MB embedding model. Let it finish fully before continuing.

#### Step 4 · Add your Groq API key
Add it in page api.py, 
```
GROK_API_KEY = os.getenv("GROK_API_KEY", "ENTER_YOUR_API(gsk_)")
```
Replace ENTER_YOUR_API(gsk_) with your actual API

Open **http://localhost:8000** in your browser. You're live. 🎉

---

### Option B — Full Setup (best accuracy, all 300+ BIS pages)

Complete Steps 1–4 from Option A first, then continue below.

#### Step 5 · Crawl the BIS website

```bash
python crawler.py
```

This visits every page on bis.gov.in, strips Hindi content, and saves clean English text to `crawled_data.json`.

⏳ Takes **10–20 minutes** depending on your internet speed.

#### Step 6 · Build the vector database

```bash
python ingest.py
```

This splits pages into chunks, converts them to vector embeddings, and stores everything in a local ChromaDB database at `./chroma_db/`.

⏳ Takes **3–5 minutes**.

#### Step 7 · Start the full API

```bash
python api.py
```

Open **http://localhost:8000** — now powered by the full BIS website index. 🎉

---

## 💡 How to Use BISBot

### Asking questions

Type your question in the input box at the bottom and press **Enter** (or click the send button).

**Good questions to ask:**
- *"What is BIS and what are its core functions?"*
- *"How do I apply for a BIS certification for my product?"*
- *"What is the Hallmarking scheme and how does it work?"*
- *"What schemes does BIS offer?"*
- *"What laboratory services does BIS provide?"*
- *"How can I file a grievance with BIS?"*
- *"What is the Compulsory Registration Scheme?"*
- *"What is BIS doing in the area of consumer awareness?"*
- *"What is the Foreign Manufacturers Certification Scheme?"*
- *"What does the BIS Act 2016 say?"*

### Multi-turn conversations

BISBot remembers the conversation. You can ask follow-up questions:

```
You:     What schemes does BIS offer?
BISBot:  BIS offers several schemes: 1. ISI Mark... 2. Hallmarking...
         3. CRS... 4. FMCS... 5. Eco Mark...

You:     Tell me more about the third one.
BISBot:  The Compulsory Registration Scheme (CRS) applies to...
```

### Quick questions (sidebar)

Click any suggestion in the left sidebar to instantly send that question.

### Copying responses

- Click **Copy** under any bot response to copy just that answer
- Click the **⎘** button in the header to copy the full conversation

### Starting fresh

- Click **New Conversation** in the sidebar (or the **+** button in the header) to start a new chat
- Click **✕** in the header to clear the current chat

### Out-of-scope questions

If you ask something unrelated to BIS (e.g., stock prices, weather, sports), BISBot will politely decline:

```
You:     What is the stock price of Tata Steel?
BISBot:  I can only answer questions about the Bureau of Indian Standards.
         Your question appears to be outside my scope. I can help with
         BIS certifications, standards, schemes, and more.
```

---

## 🏗️ How It Works (Architecture)

```
Your question
      │
      ▼
FastAPI backend
      │
      ├── Is it BIS-related?
      │         │
      │    No → Polite decline
      │         │
      │    Yes → Search ChromaDB vector database
      │              (cosine similarity — finds the most relevant
      │               content chunks from bis.gov.in)
      │                     │
      │              Top 6 matching chunks
      │                     │
      │              Groq LLaMA-3.3-70B
      │              (grounded system prompt — answer ONLY
      │               from retrieved content, cite sources)
      │                     │
      │              Stream response token by token
      │                     │
      ▼
Chat UI — renders markdown, shows source links, enables copy
```

**The full RAG pipeline:**

| Stage | Tool | What it does |
|-------|------|-------------|
| Crawl | aiohttp + BeautifulSoup | Visits every BIS page, extracts English text only |
| Chunk | Custom splitter | Splits pages into 500-word pieces with 100-word overlap |
| Embed | all-MiniLM-L6-v2 | Turns text into vectors (runs locally, free) |
| Store | ChromaDB | Saves vectors + metadata (URL, title, timestamp) |
| Retrieve | ChromaDB query | Finds top 6 most relevant chunks for your question |
| Answer | Groq LLaMA-3.3-70B | Generates a grounded, cited answer — streamed live |

---

## 🌐 API Endpoints

For developers who want to integrate BISBot into other tools:

| Method | Endpoint | What it does |
|--------|----------|-------------|
| `GET` | `/` | Opens the chat UI |
| `POST` | `/api/chat` | Send a message, get a streamed response |
| `GET` | `/api/status` | Check if the server is running + how many chunks are indexed |
| `GET` | `/api/suggestions` | Get the list of suggested starter questions |
| `GET` | `/api/conversations/{id}` | Retrieve a full conversation history |
| `DELETE` | `/api/conversations/{id}` | Clear a specific conversation |

**Example:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is BIS?", "conversation_id": null}'
```

---

## 🚢 Deploy Online

### Railway

1. Push your code to GitHub
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub**
3. Add environment variable: `GROQ_API_KEY` = `gsk_...`
4. Start command: `uvicorn demo_api:app --host 0.0.0.0 --port $PORT`
5. Done — Railway gives you a public URL

### Render

1. Go to [render.com](https://render.com) → **New Web Service** → connect your repo
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn demo_api:app --host 0.0.0.0 --port $PORT`
4. Add environment variable: `GROQ_API_KEY` = `gsk_...`
5. Click Deploy

---

## ❓ Troubleshooting

**`(bisbot-env)` not showing in terminal**
Your virtual environment isn't active. Run:
```bash
bisbot-env\Scripts\activate    # Windows
source bisbot-env/bin/activate  # Mac / Linux
```
Always do this before running any Python commands.

**`No such file or directory: demo-api.py`**
Use an underscore, not a hyphen:
```bash
python demo_api.py   ✅
python demo-api.py   ❌
```

**`ModuleNotFoundError`**
The `bisbot-env` isn't active, or dependencies weren't installed inside it:
```bash
# Activate first, then:
pip install -r requirements.txt
```

**`Connection refused` when opening the app**
The server isn't running. Start it first:
```bash
python demo_api.py
```
Then open http://localhost:8000

**Groq API errors / 401 Unauthorized**
Your API key isn't set, or it's wrong. Check:
```bash
echo %GROQ_API_KEY%   # Windows
echo $GROQ_API_KEY    # Mac / Linux
```
Get a fresh key from [console.groq.com](https://console.groq.com)

**Very slow first startup (30–60 seconds)**
Normal on first run — `sentence-transformers` downloads the embedding model (~90MB). It's cached after the first time.

**Port 8000 already in use**
```bash
uvicorn demo_api:app --port 8001
# Then open http://localhost:8001
```

**Accidentally committed `.venv` to GitHub**
```bash
git rm -r --cached bisbot-env/
git add .
git commit -m "Remove .venv from tracking"
git push
```

---

## 📦 Dependencies

```
aiohttp              # Async HTTP — makes the crawler fast
beautifulsoup4       # Parses HTML, extracts clean text
chromadb             # Local vector database
sentence-transformers # Embedding model (all-MiniLM-L6-v2, runs locally)
fastapi              # Web framework for the API
uvicorn              # ASGI server that runs FastAPI
openai               # OpenAI-compatible SDK — works with Groq
pydantic             # Request/response data validation
lxml                 # Fast HTML parser
python-dotenv        # Loads .env file automatically
```

---

## 🤝 Contributing

1. Fork the repo
2. Create a branch: `git checkout -b feature/your-idea`
3. Make your changes and commit: `git commit -m "Add your feature"`
4. Push: `git push origin feature/your-idea`
5. Open a Pull Request

**Ideas welcome:**
- PDF crawling support
- Hindi language query support
- Hybrid search (keyword + semantic)
- Thumbs up / down feedback system
- More pre-loaded BIS topics in `demo_api.py`

---

## 📄 License

MIT — free to use, modify, and distribute.

---

## 🙏 Credits

| What | Who / Where |
|------|------------|
| BIS website content | [bis.gov.in](https://www.bis.gov.in) |
| LLM | [Groq](https://groq.com) — LLaMA-3.3-70B |
| Embeddings | [sentence-transformers](https://www.sbert.net/) — all-MiniLM-L6-v2 |
| Vector DB | [ChromaDB](https://www.trychroma.com/) |
| UI fonts | Google Fonts — Inter, Lora, JetBrains Mono |

---

<div align="center">

Built with ❤️ for **FOSS × BIS Hackathon 2026**

[bis.gov.in](https://www.bis.gov.in) · [Report a bug](https://github.com/YOUR_USERNAME/bis-chatbot/issues) · [Request a feature](https://github.com/YOUR_USERNAME/bis-chatbot/issues)

</div>
