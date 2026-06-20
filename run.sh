#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── 1. Check .env ──────────────────────────────────────────────────────────
if [[ ! -f .env ]]; then
  echo "⚠️  .env not found. Copying from .env.example..."
  cp .env.example .env
  echo "✏️  Edit .env and fill in your API keys, then re-run this script."
  exit 1
fi

# Check required keys
for key in OPENAI_API_KEY TAVILY_API_KEY OPENWEATHERMAP_API_KEY GOOGLE_MAPS_API_KEY; do
  val=$(grep -E "^${key}=" .env | cut -d'=' -f2- | tr -d '[:space:]')
  if [[ -z "$val" || "$val" == sk-... || "$val" == tvly-... || "$val" == "..." ]]; then
    echo "❌  Missing or placeholder value for $key in .env"
    exit 1
  fi
done

# ── 2. Python venv ─────────────────────────────────────────────────────────
if [[ ! -d .venv ]]; then
  echo "📦 Creating virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate

echo "📦 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# ── 3. Ingest knowledge base (skip if vector_db already populated) ─────────
if [[ ! -d vector_db ]] || [[ -z "$(ls -A vector_db 2>/dev/null)" ]]; then
  echo "🗂️  Ingesting travel knowledge into ChromaDB..."
  python scripts/ingest.py
else
  echo "✅ ChromaDB already populated (vector_db/ exists). Skipping ingest."
  echo "   Run with --reingest to force re-ingestion."
fi

# --reingest flag
if [[ "${1:-}" == "--reingest" ]]; then
  echo "🔄 Re-ingesting knowledge base..."
  python scripts/ingest.py --reset
fi

# ── 4. Langfuse (optional) ────────────────────────────────────────────────
langfuse_key=$(grep -E "^LANGFUSE_PUBLIC_KEY=" .env | cut -d'=' -f2- | tr -d '[:space:]')
if [[ -n "$langfuse_key" && "$langfuse_key" != pk-lf-... ]]; then
  echo "📊 Langfuse configured — traces will be sent to $(grep LANGFUSE_HOST .env | cut -d'=' -f2-)"
else
  echo "ℹ️  Langfuse not configured (optional). Skipping."
fi

# ── 5. Launch Streamlit ────────────────────────────────────────────────────
echo ""
echo "🚀 Starting Multi-Agent AI Travel Planner..."
echo "   Open http://localhost:8501 in your browser"
echo ""

streamlit run ui/streamlit_app.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  --server.headless true
