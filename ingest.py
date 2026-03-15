"""
BIS RAG Ingestion Pipeline
Chunks crawled content → Embeds → Stores in ChromaDB vector database
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import List, Dict

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from sentence_transformers import SentenceTransformer

CRAWLED_FILE = "crawled_data.json"
CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "bis_knowledge"
CHUNK_SIZE = 500        # tokens (~400 words)
CHUNK_OVERLAP = 100     # overlap between chunks
EMBED_MODEL = "all-MiniLM-L6-v2"  # Fast, free, good quality


def word_chunks(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping word-based chunks."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = ' '.join(words[i:i + size])
        if len(chunk.strip()) > 50:  # Skip tiny chunks
            chunks.append(chunk)
        i += (size - overlap)
    return chunks


def ingest_documents(crawled_file: str = CRAWLED_FILE):
    """Load crawled data, chunk it, embed it, and store in ChromaDB."""

    print("📂 Loading crawled data...")
    with open(crawled_file, 'r', encoding='utf-8') as f:
        pages = json.load(f)
    print(f"   Loaded {len(pages)} pages\n")

    print("🔧 Setting up ChromaDB...")
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # Delete existing collection if reinserting
    try:
        client.delete_collection(COLLECTION_NAME)
        print("   Cleared existing collection")
    except Exception:
        pass

    embed_fn = SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"}
    )
    print(f"   Collection '{COLLECTION_NAME}' ready\n")

    total_chunks = 0
    doc_ids = []
    doc_texts = []
    doc_metas = []

    print("✂️  Chunking documents...")
    for page in pages:
        url = page.get('url', '')
        title = page.get('title', 'BIS Page')
        content = page.get('content', '')
        timestamp = page.get('timestamp', '')

        if not content:
            continue

        # Prepend title to content for better context
        full_text = f"Title: {title}\n{content}"
        chunks = word_chunks(full_text)

        for i, chunk in enumerate(chunks):
            chunk_id = f"{re.sub(r'[^a-zA-Z0-9]', '_', url)[:80]}_{i}"
            doc_ids.append(chunk_id)
            doc_texts.append(chunk)
            doc_metas.append({
                "url": url,
                "title": title,
                "chunk_index": i,
                "timestamp": timestamp,
                "source": "bis.gov.in"
            })
            total_chunks += 1

    print(f"   Total chunks: {total_chunks}\n")

    # Upsert in batches
    BATCH = 100
    print("💾 Embedding and storing chunks...")
    for i in range(0, len(doc_ids), BATCH):
        batch_end = min(i + BATCH, len(doc_ids))
        collection.upsert(
            ids=doc_ids[i:batch_end],
            documents=doc_texts[i:batch_end],
            metadatas=doc_metas[i:batch_end]
        )
        pct = (batch_end / total_chunks) * 100
        print(f"   Progress: {batch_end}/{total_chunks} ({pct:.0f}%)")

    print(f"\n✅ Ingestion complete!")
    print(f"   Chunks stored: {total_chunks}")
    print(f"   Vector DB: {CHROMA_DIR}")
    return collection


def retrieve(query: str, k: int = 5) -> List[Dict]:
    """Retrieve top-k relevant chunks for a query."""
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    embed_fn = SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
    collection = client.get_collection(name=COLLECTION_NAME, embedding_function=embed_fn)

    results = collection.query(
        query_texts=[query],
        n_results=k,
        include=["documents", "metadatas", "distances"]
    )

    chunks = []
    for i, (doc, meta, dist) in enumerate(zip(
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    )):
        chunks.append({
            "content": doc,
            "url": meta.get("url", ""),
            "title": meta.get("title", ""),
            "score": 1 - dist,  # Convert distance to similarity
            "timestamp": meta.get("timestamp", "")
        })
    return chunks


if __name__ == "__main__":
    if not Path(CRAWLED_FILE).exists():
        print(f"❌ '{CRAWLED_FILE}' not found. Run crawler.py first.")
        sys.exit(1)
    ingest_documents()

    # Quick test
    print("\n🔍 Test retrieval: 'BIS certification process'")
    results = retrieve("BIS certification process")
    for r in results:
        print(f"  [{r['score']:.3f}] {r['title'][:50]} — {r['url'][:60]}")
