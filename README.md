# Multi-Agent AI Travel Planner

DDM501 Lab 3 & Lab 4 submission — a multi-agent travel planning system built with LangGraph, GPT-4o-mini, ChromaDB (local RAG), and self-hosted Langfuse observability.

## Architecture

```
User Input
    │
    ▼
┌─────────────┐
│  Supervisor  │  ← Semantic router (JSON output, intent classification)
└─────┬───────┘
      │
  route?
  ┌───┴──────────┐
  │              │
  ▼              ▼
┌──────────┐  ┌──────────────────────┐
│ General  │  │ Travel Knowledge     │
│ Agent    │  │ Agent                │
│ (LLM)   │  │ (RAG + Tavily)       │
└────┬─────┘  └──────────┬───────────┘
     │                   │
     ▼                   ▼
  final_response    ┌────────────┐
                    │  Planner   │
                    │  Agent     │
                    │ (Weather + │
                    │  Maps +    │
                    │  Budget)   │
                    └────┬───────┘
                         │
                         ▼
                    final_response
```

### Agents

| Agent | Tools | Responsibility |
|---|---|---|
| **Supervisor** | None | Semantic routing + entity extraction |
| **General Agent** | None | Greetings, tips, visa, etiquette |
| **Travel Knowledge Agent** | `rag_search`, `tavily_search` | Destination information retrieval |
| **Planner Agent** | `get_weather`, `get_distance`, `calculate_budget` | Itinerary + budget generation |

### Lab 3 Requirements Met
- [x] Multi-agent architecture with ≥2 agents
- [x] Semantic router (Supervisor with JSON output)
- [x] LangGraph StateGraph with MemorySaver (persistent chat history)
- [x] Route metadata displayed in UI
- [x] ≥6 routing unit tests (`tests/test_routing.py`)
- [x] RAG with ChromaDB + local sentence-transformers embeddings

### Lab 4 Requirements Met
- [x] Self-hosted Langfuse via Docker Compose (`docker-compose.yml`)
- [x] UUID trace_id per request
- [x] Session ID and user_id metadata in traces
- [x] Route tag in Langfuse traces
- [x] 👍/👎 feedback buttons in UI
- [x] Graceful degradation when Langfuse not configured
- [x] ≥4 observability unit tests (`tests/test_observability.py`)

---

## Quick Start

### 1. Prerequisites

- Python 3.11+
- Docker + Docker Compose (for Langfuse, Lab 4)

### 2. Install dependencies

```bash
cd src/Travel-Agent
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in your API keys
```

Required keys:
```
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
OPENWEATHERMAP_API_KEY=...
GOOGLE_MAPS_API_KEY=...
```

### 4. Ingest travel knowledge (first run)

```bash
python scripts/ingest.py
# Optional: reset and re-ingest
python scripts/ingest.py --reset
```

This loads 6 Vietnamese destination guides into ChromaDB at `./vector_db/`.

### 5. Start Langfuse (Lab 4, optional)

```bash
docker compose up -d
```

Then open [http://localhost:3000](http://localhost:3000), create a project, and copy the API keys into `.env`:
```
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3000
```

### 6. Launch the app

```bash
python main.py
# or directly:
streamlit run ui/streamlit_app.py
```

Open [http://localhost:8501](http://localhost:8501).

---

## Example Queries

**General (routed to General Agent):**
- "Xin chào!"
- "Đi biển cần mang theo những gì?"
- "Visa Việt Nam cần những giấy tờ gì?"

**Travel planning (routed to Knowledge + Planner):**
- "Lên kế hoạch 3 ngày tại Đà Nẵng, ngân sách 5 triệu"
- "Tôi muốn đi Hội An 2 ngày, thích ẩm thực và văn hóa"
- "Kế hoạch 5 ngày Hà Nội cho cặp đôi, ngân sách 10 triệu"

---

## Running Tests

```bash
# From Travel-Agent/ directory
pytest tests/ -v

# Individual suites
pytest tests/test_routing.py -v        # Lab 3 routing tests (≥6)
pytest tests/test_observability.py -v  # Lab 4 observability tests (≥4)
pytest tests/test_tools.py -v
pytest tests/test_agents.py -v
```

---

## Project Structure

```
Travel-Agent/
├── app/
│   ├── config.py          # Environment variable management
│   ├── state.py           # TravelState (TypedDict + MemorySaver)
│   ├── supervisor.py      # Semantic router node
│   ├── router.py          # Conditional edge function
│   ├── graph.py           # StateGraph assembly
│   └── observability.py   # Langfuse handler + feedback
├── agents/
│   ├── general_agent.py
│   ├── travel_knowledge_agent.py
│   └── planner_agent.py
├── tools/
│   ├── budget.py          # Pure calculation
│   ├── weather.py         # OpenWeatherMap
│   ├── tavily.py          # Tavily + LLM summarization
│   ├── maps.py            # Google Maps Distance Matrix
│   └── rag.py             # ChromaDB + sentence-transformers
├── data/destinations/     # 6 Vietnamese destination guides
├── prompts/               # System prompts for each agent
├── scripts/
│   └── ingest.py          # ChromaDB ingestion pipeline
├── tests/
│   ├── test_routing.py    # 8 routing tests (Lab 3)
│   ├── test_tools.py      # Tool unit tests
│   ├── test_agents.py     # Agent scope tests
│   └── test_observability.py  # 7 observability tests (Lab 4)
├── ui/
│   └── streamlit_app.py   # Streamlit UI
├── docker-compose.yml     # Self-hosted Langfuse + PostgreSQL
├── main.py                # Entry point
├── requirements.txt
└── .env.example
```

---

## Tech Stack

| Component | Technology |
|---|---|
| LLM | GPT-4o-mini via LangChain OpenAI |
| Orchestration | LangGraph (StateGraph + MemorySaver) |
| Vector DB | ChromaDB (persistent local) |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 (local) |
| Real-time search | Tavily API |
| Weather | OpenWeatherMap API |
| Maps | Google Maps Distance Matrix API |
| UI | Streamlit |
| Observability | Langfuse (self-hosted via Docker) |
| Tests | pytest + pytest-mock |
