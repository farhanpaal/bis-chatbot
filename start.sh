#!/bin/bash
# BISBot — Full Setup Script
# Run this once to crawl, ingest, and start the server

set -e

echo "╔══════════════════════════════════════════╗"
echo "║   BISBot — FOSS × BIS Hackathon 2026   ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Check API key
if [ -z "$GROK_API_KEY" ]; then
  echo "⚠️  GROK_API_KEY not set!"
  echo "   export GROK_API_KEY='your_key_here'"
  echo "   Get yours from: https://console.x.ai/"
  echo ""
  read -p "Enter Grok API key: " GROK_API_KEY
  export GROK_API_KEY
fi

# Install deps
echo "📦 Installing dependencies..."
pip install -r requirements.txt -q

# Crawl (skip if data exists)
if [ ! -f "crawled_data.json" ]; then
  echo ""
  echo "🌐 Crawling BIS website (this takes ~10 mins)..."
  python crawler.py
else
  echo "✅ crawled_data.json found — skipping crawl"
fi

# Ingest (skip if DB exists)
if [ ! -d "chroma_db" ]; then
  echo ""
  echo "💾 Ingesting into vector database..."
  python ingest.py
else
  echo "✅ chroma_db found — skipping ingestion"
fi

# Start server
echo ""
echo "🚀 Starting BISBot API server..."
echo "   Open: http://localhost:8000"
echo ""
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
