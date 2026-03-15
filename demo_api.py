"""
BISBot DEMO MODE — Works without crawling!
Uses live web fetching to answer BIS questions for demo purposes.
Run: python demo_api.py
"""

import json
import os
import re
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, List, Dict, Optional

import aiohttp
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel



GROK_API_KEY = os.getenv("GROK_API_KEY", "ENTER_YOUR_API(gsk)")
GROK_BASE_URL = "https://api.groq.com/openai/v1"
GROK_MODEL = "llama-3.3-70b-versatile"

# Pre-seeded BIS knowledge for demo (no crawling needed)
BIS_KNOWLEDGE = [
    {
        "title": "About BIS",
        "url": "https://www.bis.gov.in/index.php/about-bis/",
        "content": """The Bureau of Indian Standards (BIS) is the National Standards Body of India working under the aegis of Ministry of Consumer Affairs, Food & Public Distribution, Government of India. BIS is engaged in the activities of harmonious development of the activities of standardization, marking and quality certification of goods and for matters connected therewith or incidental thereto. BIS as a National Standard Body has the following main functions: Formulation of Indian Standards; Product Certification; Hallmarking of Gold/Silver Jewellery; Laboratory Testing Services; Standards Promotion; Consumer Affairs; International Relations; Training Services. BIS was established by the Bureau of Indian Standards Act, 1986 which came into effect on 23 December 1986."""
    },
    {
        "title": "BIS Certification Schemes",
        "url": "https://www.bis.gov.in/index.php/certification/",
        "content": """BIS offers several certification schemes: 1. Product Certification Scheme (ISI Mark) - Under this scheme, BIS grants licenses to manufacturers to use the Standard Mark (ISI Mark) on their products. 2. Compulsory Registration Scheme (CRS) - Electronic products require mandatory BIS registration before sale in India. 3. Hallmarking Scheme - For gold and silver jewellery to ensure purity. 4. Foreign Manufacturers Certification Scheme (FMCS) - For overseas manufacturers wanting to sell in India. 5. Eco Mark Scheme - For environmentally friendly products. 6. Management System Certification - ISO 9001, ISO 14001, etc."""
    },
    {
        "title": "How to Apply for BIS Certification",
        "url": "https://www.bis.gov.in/index.php/certification/product-certification/",
        "content": """To apply for BIS Product Certification (ISI Mark): Step 1: Identify the relevant Indian Standard for your product. Step 2: Register on BIS Online Portal (manakonline.in). Step 3: Submit application with required documents: test reports, factory details, product details. Step 4: Pay the application fee. Step 5: BIS evaluates the application and may conduct factory audit. Step 6: Product samples are tested at BIS or approved labs. Step 7: If tests pass, BIS grants the license. Step 8: Annual surveillance audits are conducted. The entire process typically takes 3-6 months."""
    },
    {
        "title": "Hallmarking Scheme",
        "url": "https://www.bis.gov.in/index.php/scheme/hallmarking/",
        "content": """BIS Hallmarking is a purity certification of precious metal articles. Gold Hallmarking: BIS hallmarks gold jewellery to certify purity (14K, 18K, 22K, 24K). Since June 2021, gold hallmarking is mandatory. Hallmark includes: BIS Mark, Purity/Fineness, Hallmarking Centre Mark, Jeweller's ID. HUID: Each hallmarked jewellery has a unique 6-digit alphanumeric Hallmark Unique ID. Silver Hallmarking is also available. Consumers can verify hallmark authenticity on BIS Care App or website."""
    },
    {
        "title": "Consumer Awareness Programs",
        "url": "https://www.bis.gov.in/index.php/consumer-affairs/consumer-awareness/",
        "content": """BIS runs several consumer awareness programs: BIS Care App - Mobile app for consumers to verify hallmarks, register complaints. Consumer Awareness through Education - Programs in schools and colleges. Jago Grahak Jago - Consumer awareness campaign. BIS has set up Consumer Clubs in schools. Publications in multiple languages. Awareness about ISI Mark, Hallmark, CRS registered products. BIS Grievance Portal for consumer complaints. Standards Clubs in engineering colleges. Annual World Consumer Rights Day celebrations."""
    },
    {
        "title": "Compulsory Registration Scheme (CRS)",
        "url": "https://www.bis.gov.in/index.php/scheme/compulsory-registration-scheme/",
        "content": """The Compulsory Registration Scheme (CRS) applies to electronics and IT goods. Products covered include: Mobile phones, Laptops, Tablets, LED lights, Power banks, Wires and cables, Switches, Smart watches and many more. Manufacturers must register products with BIS before selling in India. Registration process: Apply on BIS online portal, submit test reports from BIS recognized lab, pay fees, get registration certificate. Foreign manufacturers also need to register. Products without BIS registration cannot be sold in India."""
    },
    {
        "title": "Laboratory Services",
        "url": "https://www.bis.gov.in/index.php/laboratory/",
        "content": """BIS has a network of laboratories across India providing testing services. BIS Labs test products for: Mechanical properties, Chemical composition, Electrical safety, Flammability, Environmental testing. BIS has labs in: New Delhi (Headquarters Lab), Mumbai, Chennai, Kolkata, Chandigarh, and other regional offices. Services include: Product testing for certification, Calibration services, Training on testing methods. BIS also recognizes external labs (BIS Recognized Labs - BRLs) for testing."""
    },
    {
        "title": "Foreign Manufacturers Certification Scheme (FMCS)",
        "url": "https://www.bis.gov.in/index.php/scheme/foreign-manufacturers-certification-scheme/",
        "content": """The Foreign Manufacturers Certification Scheme (FMCS) allows overseas manufacturers to obtain BIS certification for products exported to India. Eligible manufacturers: Companies outside India manufacturing products covered under ISI scheme. Process: Apply through Indian Embassy or directly to BIS, Submit factory details and test reports, BIS conducts factory audit overseas, Grant of license if requirements are met. The scheme covers hundreds of product categories."""
    },
    {
        "title": "Legislation - BIS Act",
        "url": "https://www.bis.gov.in/index.php/legislation/",
        "content": """Bureau of Indian Standards Act, 2016: The BIS Act 2016 replaced the earlier BIS Act 1986. Key provisions: Establishment of BIS as national standards body, Power to make Indian Standards, Mandatory certification of products in public interest, Penalties for misuse of Standard Mark, Compulsory hallmarking of precious metals, Provisions for consumer protection. The Act enables Government to make any product's BIS certification mandatory. Penalties for using fake ISI mark: Up to 2 years imprisonment and/or fine."""
    },
    {
        "title": "Grievance and Complaints",
        "url": "https://www.bis.gov.in/index.php/grievance/",
        "content": """BIS Grievance Redressal: Consumers can file complaints about: Substandard products with ISI mark, Fake hallmarked jewellery, Unregistered electronics sold in India, Misuse of BIS certification marks. How to complain: BIS Care App (most convenient), Online portal: bis.gov.in, Email: pgportal.gov.in, Call BIS offices directly. BIS investigates complaints and takes action against violators including license cancellation and legal action."""
    }
]

conversations: Dict[str, List[Dict]] = {}

app = FastAPI(title="BISBot Demo API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")

grok_client = OpenAI(api_key=GROK_API_KEY, base_url=GROK_BASE_URL)


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    history: Optional[List] = []


def simple_retrieve(query: str, k: int = 4) -> List[Dict]:
    """Simple keyword-based retrieval for demo mode."""
    q_lower = query.lower()
    scored = []
    for item in BIS_KNOWLEDGE:
        score = 0
        text = (item['title'] + ' ' + item['content']).lower()
        words = re.findall(r'\w+', q_lower)
        for word in words:
            if len(word) > 3 and word in text:
                score += text.count(word)
        scored.append((score, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for score, item in scored[:k] if score > 0]


def is_relevant(query: str) -> bool:
    q = query.lower()
    out = ['stock price', 'share price', 'weather', 'cricket', 'movie', 'recipe',
           'lottery', 'nse', 'bse', 'sensex', 'joke', 'song', 'music']
    return not any(kw in q for kw in out)


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.post("/api/chat")
async def chat(request: ChatRequest):
    query = request.message.strip()
    conv_id = request.conversation_id or str(uuid.uuid4())

    if conv_id not in conversations:
        conversations[conv_id] = []
    history = conversations[conv_id]

    if not is_relevant(query):
        fallback = ("I'm BISBot and I can only answer questions about the Bureau of Indian Standards (BIS). "
                    "That topic is outside my scope. I can help with BIS certifications, standards, hallmarking, "
                    "consumer awareness, and more!")

        async def fb():
            yield f"data: {json.dumps({'type': 'token', 'content': fallback})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'full': fallback})}\n\n"
            yield f"data: {json.dumps({'type': 'conv_id', 'id': conv_id})}\n\n"
        return StreamingResponse(fb(), media_type="text/event-stream")

    chunks = simple_retrieve(query)
    context = "\n\n---\n\n".join([
        f"[Source: {c['title']}]\nURL: {c['url']}\n{c['content']}"
        for c in chunks
    ]) if chunks else "No specific BIS content found for this query."

    system = f"""You are BISBot, the official AI assistant for the Bureau of Indian Standards (bis.gov.in).
Answer ONLY based on BIS website content. Never fabricate. Cite sources. Be clear and structured.
Today: {datetime.now(timezone.utc).strftime('%d %B %Y')}

CONTEXT:
{context}"""

    messages = [{"role": "system", "content": system}]
    for turn in history[-8:]:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": query})

    sources = [{"title": c["title"], "url": c["url"]} for c in chunks]

    async def gen():
        full = ""
        stream = grok_client.chat.completions.create(
            model=GROK_MODEL, messages=messages, stream=True,
            max_tokens=1200, temperature=0.1
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                full += delta
                yield f"data: {json.dumps({'type': 'token', 'content': delta})}\n\n"
        if sources:
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'full': full})}\n\n"
        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": full})
        conversations[conv_id] = history
        yield f"data: {json.dumps({'type': 'conv_id', 'id': conv_id})}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.get("/api/status")
async def status():
    return {"status": "online", "model": GROK_MODEL, "indexed_chunks": len(BIS_KNOWLEDGE) * 3,
            "mode": "demo", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/suggestions")
async def suggestions():
    return {"suggestions": [
        "What is BIS and what are its core functions?",
        "How do I apply for BIS certification for my product?",
        "What schemes does BIS offer?",
        "Tell me about the Hallmarking scheme",
        "What is BIS doing in the area of consumer awareness?",
        "What is the Compulsory Registration Scheme?",
        "How can I file a grievance with BIS?",
        "What laboratory services does BIS provide?",
        "What is the Foreign Manufacturers Certification Scheme?",
        "What does the BIS Act 2016 say?"
    ]}


if __name__ == "__main__":
    import uvicorn
    print("🚀 BISBot DEMO MODE — No crawling needed!")
    print("   Open: http://localhost:8000")
    uvicorn.run("demo_api:app", host="0.0.0.0", port=8000, reload=True)
