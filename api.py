"""
BIS AI Chatbot — FastAPI Backend
Grok API + ChromaDB RAG + Conversation Memory + Streaming
"""

import json
import os
import re
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, List, Dict, Optional

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI  # Grok uses OpenAI-compatible API
from pydantic import BaseModel

# ─── Config ────────────────────────────────────────────────────────────────────
GROK_API_KEY = os.getenv("GROK_API_KEY", "ENTER_YOUR_API(gsk_)")
GROK_BASE_URL = "https://api.groq.com/openai/v1"
GROK_MODEL = "llama-3.3-70b-versatile"

CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "bis_knowledge"
EMBED_MODEL = "all-MiniLM-L6-v2"
TOP_K = 6  # Chunks to retrieve
MAX_HISTORY = 10  # Turns to keep in memory

# BIS relevance — topics the bot handles
BIS_TOPICS = [
    "bis", "bureau of indian standards", "certification", "hallmark", "hallmarking",
    "is mark", "isi mark", "standard", "scheme", "laboratory", "testing", "quality",
    "consumer", "product", "license", "registration", "india", "bis.gov.in",
    "compulsory registration", "eco mark", "fmcs", "foreign manufacturer",
    "publication", "press release", "legislation", "act", "grievance", "complaint",
    "wearable", "electronics", "textile", "food", "steel", "cement", "toy",
    "conformity", "accreditation", "sample", "fee", "application", "form"
]

# ─── Models ─────────────────────────────────────────────────────────────────────
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    history: Optional[List[ChatMessage]] = []

class FeedbackRequest(BaseModel):
    conversation_id: str
    message_index: int
    rating: str  # "good" | "bad"

# ─── In-memory conversation store ───────────────────────────────────────────────
# In production, swap with Redis or a DB
conversations: Dict[str, List[Dict]] = {}

# ─── App ─────────────────────────────────────────────────────────────────────────
app = FastAPI(title="BIS AI Chatbot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Grok Client ─────────────────────────────────────────────────────────────────
grok_client = OpenAI(api_key=GROK_API_KEY, base_url=GROK_BASE_URL)

# ─── Vector DB ───────────────────────────────────────────────────────────────────
chroma_client = None
collection = None

@app.on_event("startup")
async def startup_event():
    global chroma_client, collection
    try:
        chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
        embed_fn = SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
        collection = chroma_client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=embed_fn
        )
        count = collection.count()
        print(f"✅ ChromaDB loaded — {count} chunks indexed")
    except Exception as e:
        print(f"⚠️  ChromaDB not available: {e}")
        print("   Run ingest.py first, or start in demo mode")


# ─── Retrieval ───────────────────────────────────────────────────────────────────
def retrieve_context(query: str, k: int = TOP_K) -> List[Dict]:
    """Retrieve top-k relevant chunks from vector DB."""
    if not collection:
        return []
    try:
        results = collection.query(
            query_texts=[query],
            n_results=k,
            include=["documents", "metadatas", "distances"]
        )
        chunks = []
        seen_urls = set()
        for doc, meta, dist in zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ):
            url = meta.get("url", "")
            score = round(1 - dist, 3)
            chunks.append({
                "content": doc,
                "url": url,
                "title": meta.get("title", "BIS"),
                "score": score,
                "timestamp": meta.get("timestamp", "")
            })
            seen_urls.add(url)
        return chunks
    except Exception as e:
        print(f"Retrieval error: {e}")
        return []


def is_bis_relevant(query: str, chunks: List[Dict]) -> bool:
    """
    Determine if query is relevant to BIS.
    Uses both keyword check and retrieval score.
    """
    q_lower = query.lower()

    # Hard out-of-scope signals
    out_of_scope = [
        "stock price", "share price", "weather", "cricket score", "movie",
        "recipe", "lottery", "nse", "bse", "sensex", "nifty", "joke",
        "song", "music", "politics", "election", "covid vaccine"
    ]
    if any(kw in q_lower for kw in out_of_scope):
        return False

    # If we got high-scoring chunks, it's relevant
    if chunks and chunks[0]['score'] > 0.35:
        return True

    # Keyword match
    if any(kw in q_lower for kw in BIS_TOPICS):
        return True

    # Low-scoring chunks with no keyword match = not relevant
    if chunks and chunks[0]['score'] < 0.25:
        return False

    return True


def build_system_prompt(chunks: List[Dict]) -> str:
    """Build the grounding system prompt with retrieved context."""
    context_blocks = []
    cited_urls = []

    for i, chunk in enumerate(chunks, 1):
        context_blocks.append(
            f"[Source {i}]: {chunk['title']}\nURL: {chunk['url']}\n{chunk['content']}"
        )
        if chunk['url'] not in cited_urls:
            cited_urls.append(chunk['url'])

    context_str = "\n\n---\n\n".join(context_blocks)

    return f"""You are BISBot — the official AI assistant for the Bureau of Indian Standards (BIS), India's national standards body (bis.gov.in).

You ONLY answer questions based on the retrieved BIS website content provided below.
You must NEVER fabricate facts, invent regulations, or guess. If the answer is not in the context, say so clearly.

RULES:
1. Ground every answer in the provided context chunks.
2. Always cite sources using [Source N] notation and include the URL at the end.
3. If a question is unrelated to BIS (e.g., stock prices, sports, entertainment), politely decline and suggest a relevant BIS topic.
4. Use clear, structured formatting (bullet points, numbered steps) when explaining processes.
5. For multi-turn conversations, maintain context from previous messages.
6. Keep answers concise but complete — aim for clarity over verbosity.
7. If asked about latest updates/news, prioritize the most recently timestamped chunks.

RETRIEVED CONTEXT:
{context_str}

Today's date: {datetime.now(timezone.utc).strftime('%d %B %Y')}
"""


def build_fallback_response(query: str) -> str:
    """Response for out-of-scope queries."""
    return (
        "I'm BISBot, and I can only answer questions related to the **Bureau of Indian Standards (BIS)** "
        "and the content on [bis.gov.in](https://www.bis.gov.in).\n\n"
        f"Your question about *\"{query}\"* appears to be outside my scope.\n\n"
        "I can help you with topics like:\n"
        "- 🏷️ **Product Certification** (ISI Mark, BIS schemes)\n"
        "- ⚗️ **Laboratory & Testing Services**\n"
        "- 📋 **Indian Standards development**\n"
        "- 👤 **Consumer Affairs & Awareness**\n"
        "- 🌐 **International Relations**\n"
        "- 📰 **Press Releases & Publications**\n"
        "- ⚖️ **Legislation & Acts**\n\n"
        "What would you like to know about BIS?"
    )


# ─── Streaming Chat ───────────────────────────────────────────────────────────────
async def stream_response(
    query: str,
    history: List[Dict],
    chunks: List[Dict]
) -> AsyncGenerator[str, None]:
    """Stream response from Grok with RAG context."""

    system_prompt = build_system_prompt(chunks)

    # Build messages array
    messages = [{"role": "system", "content": system_prompt}]

    # Add conversation history (last N turns)
    for turn in history[-MAX_HISTORY:]:
        messages.append({"role": turn["role"], "content": turn["content"]})

    # Add current query
    messages.append({"role": "user", "content": query})

    # Collect sources to append
    unique_sources = []
    seen = set()
    for chunk in chunks:
        if chunk['url'] not in seen:
            unique_sources.append({"title": chunk['title'], "url": chunk['url']})
            seen.add(chunk['url'])

    try:
        stream = grok_client.chat.completions.create(
            model=GROK_MODEL,
            messages=messages,
            stream=True,
            max_tokens=1500,
            temperature=0.1,  # Low temp for factual accuracy
        )

        full_response = ""
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                full_response += delta
                yield f"data: {json.dumps({'type': 'token', 'content': delta})}\n\n"

        # Send sources after response
        if unique_sources:
            yield f"data: {json.dumps({'type': 'sources', 'sources': unique_sources[:5]})}\n\n"

        yield f"data: {json.dumps({'type': 'done', 'full': full_response})}\n\n"

    except Exception as e:
        error_msg = f"I encountered an error: {str(e)}. Please try again."
        yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"


# ─── Routes ───────────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Main chat endpoint with streaming."""
    query = request.message.strip()
    conv_id = request.conversation_id or str(uuid.uuid4())

    if not query:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Load or create conversation
    if conv_id not in conversations:
        conversations[conv_id] = []

    history = conversations[conv_id]

    # Retrieve relevant chunks
    chunks = retrieve_context(query)

    # Check relevance
    if not is_bis_relevant(query, chunks):
        fallback = build_fallback_response(query)
        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": fallback, "timestamp": datetime.utcnow().isoformat()})
        conversations[conv_id] = history

        async def fallback_stream():
            yield f"data: {json.dumps({'type': 'token', 'content': fallback})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'full': fallback})}\n\n"
            yield f"data: {json.dumps({'type': 'conv_id', 'id': conv_id})}\n\n"

        return StreamingResponse(fallback_stream(), media_type="text/event-stream")

    async def response_generator():
        full_response = ""
        async for event in stream_response(query, history, chunks):
            yield event
            # Capture full response for history
            if event.startswith("data: "):
                try:
                    data = json.loads(event[6:])
                    if data.get("type") == "done":
                        full_response = data.get("full", "")
                except Exception:
                    pass

        # Save to conversation history
        history.append({"role": "user", "content": query, "timestamp": datetime.utcnow().isoformat()})
        history.append({"role": "assistant", "content": full_response, "timestamp": datetime.utcnow().isoformat()})
        conversations[conv_id] = history

        yield f"data: {json.dumps({'type': 'conv_id', 'id': conv_id})}\n\n"

    return StreamingResponse(response_generator(), media_type="text/event-stream")


@app.get("/api/conversations/{conv_id}")
async def get_conversation(conv_id: str):
    """Retrieve full conversation history."""
    if conv_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"conversation_id": conv_id, "messages": conversations[conv_id]}


@app.delete("/api/conversations/{conv_id}")
async def clear_conversation(conv_id: str):
    """Clear a conversation's history."""
    if conv_id in conversations:
        del conversations[conv_id]
    return {"status": "cleared", "conversation_id": conv_id}


@app.get("/api/status")
async def status():
    """API health check."""
    chunk_count = collection.count() if collection else 0
    return {
        "status": "online",
        "model": GROK_MODEL,
        "indexed_chunks": chunk_count,
        "active_conversations": len(conversations),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/suggestions")
async def get_suggestions():
    """Return suggested questions for the UI."""
    return {
        "suggestions": [
            "What is BIS and what are its core functions?",
            "How do I apply for BIS certification for my product?",
            "What schemes does BIS offer?",
            "What is the Hallmarking scheme and how does it work?",
            "What is BIS doing in the area of consumer awareness?",
            "How can I file a grievance with BIS?",
            "What is the Compulsory Registration Scheme (CRS)?",
            "What are the fees for BIS product certification?",
            "How does the Foreign Manufacturers Certification Scheme work?",
            "What laboratory services does BIS provide?",
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
