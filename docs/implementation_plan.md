# Implementation Plan: Multi-Agent Travel Planning System

**Version:** 1.1  
**Status:** PENDING APPROVAL  
**Tech Stack:** LangGraph · LangChain · gpt-4o-mini · ChromaDB · Tavily · Gradio · **Langfuse**

---

## Dependency Graph

```
Wave 0 (parallel):  T0.1 ──┐  T1.1  T1.2  T0.2  T0.5(Langfuse)
                            │
Wave 1 (parallel):  T0.3 ◄─┤  T0.4
                            │
Wave 2 (parallel):  T2.1  T2.2  T2.3  T2.4  T2.5 ◄── T1.1
                                                │
Wave 3:             T3.1 ◄─────────────────────┘
                     │
Wave 4:             T3.2
                     │
Wave 5 (parallel):  T4.1  T4.2 ◄── T3.2+T2.3+T2.5  T4.3 ◄── T2.1+T2.2+T2.4  T4.4
                                                                                  │
Wave 6:             T5.1 ◄────────────────────────────────────────────────────────┘
                     │
Wave 7:             T5.2 ◄── T4.1+T4.2+T4.3+T4.4+T0.5
                     │
Wave 8 (parallel):  T6.1  T7.3 ◄── T7.1  T7.2
```

---

## Phase 0 — Foundation

### T0.1 — Project Structure & Dependencies
**Mô tả:** Tạo toàn bộ thư mục và file `requirements.txt`.

**Depends on:** _(không có)_  
**Blocks:** T0.3, T0.4, T2.1, T2.2, T2.3, T2.4, T2.5

**Cấu trúc cần tạo:**
```
travel-agent/
├── app/
├── agents/
├── tools/
├── prompts/
├── data/
│   ├── destinations/
│   ├── culture/
│   ├── cuisine/
│   └── travel_guides/
├── vector_db/
├── ui/
├── tests/
├── scripts/
├── requirements.txt
└── .gitignore
```

**`requirements.txt`:**
```
langgraph>=0.2
langchain>=0.2
langchain-openai>=0.1
langchain-community>=0.2
chromadb>=0.5
sentence-transformers>=2.7
tavily-python>=0.3
googlemaps>=4.10
gradio>=4.0
python-dotenv>=1.0
requests>=2.31
langfuse>=2.0
pytest>=8.0
pytest-asyncio>=0.23
```

**Acceptance Criteria:**
- [ ] Tất cả thư mục tồn tại
- [ ] `pip install -r requirements.txt` không lỗi
- [ ] `python -c "import langgraph, langchain, chromadb, gradio"` pass

**Test Plan:**
```bash
pip install -r requirements.txt
python -c "import langgraph, langchain_openai, chromadb, gradio, sentence_transformers"
```

---

### T0.2 — `.env.example`
**Mô tả:** File template env với placeholder keys.

**Depends on:** _(không có)_  
**Blocks:** _(không có)_

**Nội dung:**
```env
# LLM
OPENAI_API_KEY=sk-...

# Search & Tools
TAVILY_API_KEY=tvly-...
OPENWEATHERMAP_API_KEY=...
GOOGLE_MAPS_API_KEY=...

# App config
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0
CHROMA_PERSIST_DIR=./vector_db
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Langfuse Observability
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

**Acceptance Criteria:**
- [ ] File tồn tại tại root project
- [ ] Có đủ 8 keys, không có giá trị thật
- [ ] `.gitignore` chứa `.env` (không chứa `.env.example`)

**Test Plan:** Review manual.

---

### T0.3 — `app/state.py` — TravelState
**Mô tả:** Định nghĩa shared state TypedDict cho toàn bộ LangGraph graph.

**Depends on:** T0.1  
**Blocks:** T4.1, T4.2, T4.3, T4.4, T5.1, T5.2

**Schema:**
```python
class TravelState(TypedDict):
    messages: list
    user_query: str
    destination: str
    travel_dates: str
    duration_days: int
    budget: float
    interests: list[str]
    rag_context: str
    tavily_context: str
    weather: dict
    travel_distances: dict
    estimated_budget: dict
    itinerary: str
    final_response: str
    route: str  # "general" | "travel"
```

**Acceptance Criteria:**
- [ ] `from app.state import TravelState` không lỗi
- [ ] Tất cả fields có type annotation đúng
- [ ] `state: TravelState = {}` không lỗi

**Test Plan:**
```bash
python -c "from app.state import TravelState; s: TravelState = {}; print('OK')"
```

---

### T0.5 — Langfuse Observability Setup
**Mô tả:** Tích hợp Langfuse để trace toàn bộ LLM calls, tool calls, và agent execution trong graph. Cho phép theo dõi latency, token usage, cost, và lỗi theo từng request.

**Depends on:** _(không có — độc lập)_  
**Blocks:** T5.2 (graph cần inject callback handler)

**Cài đặt:**
```
langfuse>=2.0  # thêm vào requirements.txt
```

**Env vars cần thêm vào `.env.example`:**
```env
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com  # hoặc self-hosted URL
```

**Cách tích hợp với LangGraph:**
```python
# app/observability.py
from langfuse.callback import CallbackHandler
from app.config import config

def get_langfuse_handler(session_id: str = None, user_id: str = None):
    return CallbackHandler(
        public_key=config.LANGFUSE_PUBLIC_KEY,
        secret_key=config.LANGFUSE_SECRET_KEY,
        host=config.LANGFUSE_HOST,
        session_id=session_id,
        user_id=user_id,
    )
```

**Cách dùng trong graph invoke (T5.2 + T6.1):**
```python
# Truyền callback handler vào mỗi request
handler = get_langfuse_handler(session_id="session-123")
result = graph.invoke(state, config={"callbacks": [handler]})
```

**Những gì Langfuse sẽ capture tự động:**
- Toàn bộ LLM calls (prompt, completion, model, tokens, latency)
- Tool calls từng agent (input/output)
- Trace cây đầy đủ: supervisor → knowledge agent → planner
- Cost per request (tính tự động theo gpt-4o-mini pricing)
- Error & exception với context đầy đủ

**Acceptance Criteria:**
- [ ] `from app.observability import get_langfuse_handler` không lỗi
- [ ] Sau khi chạy 1 request, trace xuất hiện trên Langfuse dashboard
- [ ] Trace hiển thị đúng cây: supervisor → (general | travel_knowledge → planner)
- [ ] Token count và latency có trong từng span
- [ ] Nếu `LANGFUSE_PUBLIC_KEY` không có: handler trả về `None`, graph vẫn chạy bình thường (graceful degradation)

**Test Plan:**
```python
def test_langfuse_handler_created():
    handler = get_langfuse_handler(session_id="test-001")
    assert handler is not None

def test_langfuse_graceful_without_key(monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    handler = get_langfuse_handler()
    assert handler is None  # không crash

def test_graph_works_without_langfuse():
    # Graph vẫn chạy khi callbacks=[]
    result = graph.invoke(state, config={"callbacks": []})
    assert result["final_response"] != ""
```

---

### T0.4 — `app/config.py` — Config Loader
**Mô tả:** Load và validate tất cả env vars. Raise lỗi rõ ràng nếu thiếu key bắt buộc.

**Depends on:** T0.1  
**Blocks:** T2.2, T2.3, T2.4, T2.5, T4.1, T4.2, T4.3, T4.4

**Pattern:**
```python
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY in .env")
```

**Acceptance Criteria:**
- [ ] `from app.config import config` không lỗi khi có `.env` đầy đủ
- [ ] Raise `ValueError` với message cụ thể khi thiếu key
- [ ] Không hardcode bất kỳ API key nào

**Test Plan:**
```bash
# Happy path
python -c "from app.config import config; print(config.LLM_MODEL)"

# Missing key
OPENAI_API_KEY="" python -c "from app.config import config"
# Expected: ValueError: Missing OPENAI_API_KEY
```

---

## Phase 1 — Data & Prompts _(song song với Phase 0)_

### T1.1 — Destination Knowledge Documents
**Mô tả:** 6 file Markdown về điểm đến phổ biến — nguồn dữ liệu cho RAG.

**Depends on:** _(không có)_  
**Blocks:** T2.5, T3.1

**Files cần tạo** (`data/destinations/`):
- `da_nang.md`, `hoi_an.md`, `ha_noi.md`, `ho_chi_minh.md`, `da_lat.md`, `phu_quoc.md`

**Cấu trúc mỗi file:**
```markdown
# [Tên điểm đến]
## Tổng quan
## Điểm tham quan nổi bật
## Ẩm thực đặc trưng
## Phương tiện di chuyển nội địa
## Thời điểm lý tưởng
## Lưu ý & tips
```

**Acceptance Criteria:**
- [ ] 6 files tồn tại, mỗi file ≥ 500 từ
- [ ] Mỗi file có đủ 6 sections
- [ ] Nội dung tiếng Việt, thông tin chính xác

**Test Plan:** Review manual từng file.

---

### T1.2 — Prompt Files
**Mô tả:** 4 system prompt markdown cho 4 agents. Mỗi prompt enforce đúng scope agent.

**Depends on:** _(không có)_  
**Blocks:** T4.1, T4.2, T4.3, T4.4

**Files cần tạo** (`prompts/`):
- `supervisor.md` — chỉ route, không trả lời trực tiếp
- `general.md` — chỉ chat thông thường, không gọi tool
- `travel_knowledge.md` — chỉ retrieve info, không lập lịch
- `planner.md` — chỉ lập lịch từ context có sẵn, không search

**Acceptance Criteria:**
- [ ] 4 files tồn tại
- [ ] Mỗi prompt có: Role, Scope, Out-of-scope, Output format
- [ ] Mỗi prompt có explicit "NEVER" constraints

**Test Plan:** Review manual.

---

## Phase 2 — Tools

### T2.1 — `tools/budget.py` — Budget Calculator
**Mô tả:** Công cụ tính toán thuần túy, không gọi API.

**Depends on:** T0.1, T0.3  
**Blocks:** T4.3, T7.1

**Interface:**
```python
@tool
def calculate_budget(
    hotel_per_night: float, nights: int,
    flights: float, food_per_day: float,
    activities: float, transport: float,
    shopping: float, total_budget: float
) -> dict: ...
```

**Acceptance Criteria:**
- [ ] Tính đúng total = sum các khoản
- [ ] `remaining = total_budget - total`
- [ ] Suggestions xuất hiện khi `remaining < 0`
- [ ] Không gọi bất kỳ external API nào
- [ ] Decorated `@tool`

**Test Plan:**
```python
def test_budget_calculation():
    result = calculate_budget.invoke({
        "hotel_per_night": 500000, "nights": 3,
        "flights": 2000000, "food_per_day": 200000,
        "activities": 500000, "transport": 300000,
        "shopping": 200000, "total_budget": 10000000
    })
    assert result["total"] == 500000*3 + 2000000 + 200000*3 + 500000 + 300000 + 200000
    assert "remaining" in result
    assert "breakdown" in result
```

---

### T2.2 — `tools/weather.py` — Weather Tool
**Mô tả:** Gọi OpenWeatherMap API, lấy forecast 5 ngày.

**Depends on:** T0.1, T0.4  
**Blocks:** T4.3, T7.1

**Interface:**
```python
@tool
def get_weather(city: str, days: int) -> dict: ...
# Output: {city, forecast: [{date, temp_min, temp_max, description, rain_mm}]}
```

**Acceptance Criteria:**
- [ ] Decorated `@tool`
- [ ] Output có `city` và `forecast` list
- [ ] Raise lỗi rõ ràng nếu city không tìm thấy (HTTP 404)
- [ ] Retry 1 lần khi timeout, sau đó raise

**Test Plan:**
```python
def test_weather_valid_city():
    result = get_weather.invoke({"city": "Da Nang", "days": 3})
    assert result["city"] == "Da Nang"
    assert len(result["forecast"]) == 3

def test_weather_invalid_city():
    with pytest.raises(Exception, match="City not found"):
        get_weather.invoke({"city": "XYZ_INVALID_123", "days": 1})
```

---

### T2.3 — `tools/tavily.py` — Tavily Search Tool
**Mô tả:** Gọi Tavily API, summarize kết quả bằng LLM trước khi trả về state.

**Depends on:** T0.1, T0.4  
**Blocks:** T4.2, T7.1

**Interface:**
```python
@tool
def tavily_search(query: str, max_results: int = 5) -> dict: ...
# Output: {summary: str (≤500 words), sources: list[str]}
```

**Acceptance Criteria:**
- [ ] Decorated `@tool`
- [ ] Summary được tạo bằng LLM call (không phải string concat)
- [ ] Nếu 0 kết quả: `{summary: "Không tìm thấy thông tin", sources: []}`
- [ ] Không dump raw JSON vào state

**Test Plan:**
```python
def test_tavily_returns_summary():
    result = tavily_search.invoke({"query": "Da Nang hotel prices 2025", "max_results": 3})
    assert isinstance(result["summary"], str)
    assert len(result["summary"]) > 50

def test_tavily_no_results():
    result = tavily_search.invoke({"query": "xyzabc123_nonexistent_place", "max_results": 3})
    assert result["summary"] is not None
```

---

### T2.4 — `tools/maps.py` — Maps Distance Tool
**Mô tả:** Gọi Google Maps Distance Matrix API.

**Depends on:** T0.1, T0.4  
**Blocks:** T4.3, T7.1

**Interface:**
```python
@tool
def get_distance(origin: str, destination: str, mode: str = "driving") -> dict: ...
# Output: {distance_km: float, duration_min: int, mode: str}
```

**Acceptance Criteria:**
- [ ] Decorated `@tool`
- [ ] Handle lỗi ZERO_RESULTS
- [ ] `distance_km` và `duration_min` > 0 với route hợp lệ

**Test Plan:**
```python
def test_maps_valid_route():
    result = get_distance.invoke({"origin": "Da Nang", "destination": "Hoi An"})
    assert 20 < result["distance_km"] < 40  # ~30km thực tế

def test_maps_invalid_route():
    with pytest.raises(Exception, match="No route"):
        get_distance.invoke({"origin": "Da Nang", "destination": "Tokyo"})
```

---

### T2.5 — `tools/rag.py` — RAG Retrieval Tool
**Mô tả:** ChromaDB retriever với HuggingFace local embedding.

**Depends on:** T0.1, T0.4, T1.1  
**Blocks:** T3.1, T4.2, T7.1

**Interface:**
```python
@tool
def rag_search(query: str, n_results: int = 3) -> dict: ...
# Output: {context: str, sources: list[str]}
```

**Acceptance Criteria:**
- [ ] Decorated `@tool`
- [ ] Dùng `sentence-transformers/all-MiniLM-L6-v2` (local, không gọi OpenAI)
- [ ] ChromaDB persist tại `CHROMA_PERSIST_DIR`
- [ ] Collection chưa có data → `{context: "", sources: []}` (không crash)

**Test Plan:**
```python
def test_rag_returns_context(populated_chroma):
    result = rag_search.invoke({"query": "ẩm thực Đà Nẵng", "n_results": 2})
    assert result["context"] != ""
    assert len(result["sources"]) > 0

def test_rag_empty_db(empty_chroma):
    result = rag_search.invoke({"query": "test", "n_results": 2})
    assert result["context"] == ""
```

---

## Phase 3 — RAG Pipeline

### T3.1 — `scripts/ingest.py` — Data Ingestion
**Mô tả:** Script one-shot: load documents → chunk → embed → store vào ChromaDB.

**Depends on:** T2.5, T1.1  
**Blocks:** T3.2

**Chunking strategy:**
- Chunk size: 500 tokens, Overlap: 50 tokens
- Metadata: `{source_file, destination_name, section}`

**Acceptance Criteria:**
- [ ] `python scripts/ingest.py` chạy không lỗi
- [ ] Log: `"Ingested X chunks from Y documents"`
- [ ] Collection `travel_knowledge` tồn tại sau khi chạy
- [ ] Idempotent: chạy 2 lần không tạo duplicate (upsert)

**Test Plan:**
```bash
python scripts/ingest.py
# Expected: "Ingested ~60-80 chunks from 6 documents"

python scripts/ingest.py  # lần 2
# Verify: count trong ChromaDB không tăng
```

---

### T3.2 — RAG Quality Validation
**Mô tả:** Chạy 5 test queries, kiểm tra retrieved chunks có relevance.

**Depends on:** T3.1  
**Blocks:** T4.2

**Test queries:**
1. `"điểm tham quan nổi tiếng ở Đà Nẵng"` → chunk từ `da_nang.md`
2. `"ẩm thực Hội An"` → chunk từ `hoi_an.md`
3. `"thời điểm đẹp để đi Đà Lạt"` → chunk từ `da_lat.md`
4. `"phương tiện di chuyển Phú Quốc"` → chunk từ `phu_quoc.md`
5. `"bún bò Huế"` → không có data → context rỗng hoặc gần nhất

**Acceptance Criteria:**
- [ ] 4/5 query đầu trả về chunk đúng nguồn
- [ ] Similarity score top-1 ≥ 0.5 cho 4 query đầu
- [ ] Query 5 không crash

**Test Plan:**
```bash
python scripts/validate_rag.py
```

---

## Phase 4 — Agents

### T4.1 — `agents/general_agent.py` — General Agent
**Mô tả:** Agent xử lý chat thông thường. Chỉ dùng LLM, không dùng tool.

**Depends on:** T0.3, T0.4, T1.2  
**Blocks:** T5.2, T7.2

**Interface:**
```python
def general_agent(state: TravelState) -> TravelState: ...
```

**Acceptance Criteria:**
- [ ] Không import bất kỳ tool nào từ `tools/`
- [ ] Cập nhật `state["final_response"]` và `state["messages"]`
- [ ] Trả lời bằng tiếng Việt, tone thân thiện

**Test Plan:**
```python
def test_general_agent_greeting():
    state = {"user_query": "Xin chào!", "messages": []}
    result = general_agent(state)
    assert result["final_response"] != ""

def test_general_agent_no_tools_called(mocker):
    mock_tool = mocker.patch("tools.rag.rag_search")
    general_agent({"user_query": "cho tôi tips du lịch"})
    mock_tool.assert_not_called()
```

---

### T4.2 — `agents/travel_knowledge_agent.py` — Travel Knowledge Agent
**Mô tả:** Tự quyết định dùng RAG, Tavily, hoặc cả hai. Chỉ retrieve — không lập lịch.

**Depends on:** T0.3, T0.4, T1.2, T2.3, T2.5, T3.2  
**Blocks:** T5.2, T7.2

**Routing logic:**
- Lịch sử/văn hóa/ẩm thực → RAG
- Giá cả/sự kiện/tin tức → Tavily
- Câu hỏi chung → cả hai

**Acceptance Criteria:**
- [ ] Cập nhật `state["rag_context"]` và/hoặc `state["tavily_context"]`
- [ ] KHÔNG cập nhật `state["itinerary"]`
- [ ] KHÔNG gọi Weather/Maps/Budget tools

**Test Plan:**
```python
def test_knowledge_agent_uses_rag_for_culture(mocker):
    mock_rag = mocker.patch("tools.rag.rag_search", return_value={"context": "...", "sources": []})
    state = {"destination": "Da Nang", "user_query": "văn hóa Đà Nẵng"}
    result = travel_knowledge_agent(state)
    mock_rag.assert_called_once()

def test_knowledge_agent_no_itinerary_in_output():
    result = travel_knowledge_agent({"destination": "Da Nang"})
    assert result.get("itinerary", "") == ""
```

---

### T4.3 — `agents/planner_agent.py` — Planner Agent
**Mô tả:** Nhận context từ state, gọi Weather/Maps/Budget, tạo lịch trình chi tiết.

**Depends on:** T0.3, T0.4, T1.2, T2.1, T2.2, T2.4  
**Blocks:** T5.2, T7.2

**Acceptance Criteria:**
- [ ] Bắt buộc gọi Weather tool nếu `travel_dates` có trong state
- [ ] Bắt buộc gọi Budget tool nếu `budget` có trong state
- [ ] Output `state["itinerary"]` có đủ N ngày (`duration_days`)
- [ ] Mỗi ngày có: sáng/trưa/chiều/tối, địa điểm, ẩm thực, di chuyển
- [ ] KHÔNG gọi RAG hoặc Tavily

**Test Plan:**
```python
def test_planner_generates_itinerary():
    state = {
        "destination": "Da Nang", "duration_days": 3,
        "budget": 10000000, "travel_dates": "2025-08-01",
        "rag_context": "...", "tavily_context": "..."
    }
    result = planner_agent(state)
    assert "Ngày 1" in result["itinerary"]
    assert "Ngày 3" in result["itinerary"]
    assert result["estimated_budget"]["total"] > 0

def test_planner_no_search_tools(mocker):
    mock_tavily = mocker.patch("tools.tavily.tavily_search")
    planner_agent(full_state)
    mock_tavily.assert_not_called()
```

---

### T4.4 — `app/supervisor.py` — Supervisor Agent
**Mô tả:** Phân loại intent, route request, extract thông tin du lịch. Không trả lời user.

**Depends on:** T0.3, T0.4, T1.2  
**Blocks:** T5.1, T5.2, T7.2

**Routing:**
- `"general"`: chào hỏi, câu hỏi chung, tips, visa, packing
- `"travel"`: yêu cầu lập kế hoạch, hỏi về địa điểm + thời gian + ngân sách

**Acceptance Criteria:**
- [ ] Cập nhật `state["route"]` = `"general"` hoặc `"travel"`
- [ ] Với travel: extract `destination`, `duration_days`, `budget`, `interests`
- [ ] KHÔNG cập nhật `final_response`
- [ ] Đúng 10/10 test cases routing

**Test Plan:**
```python
@pytest.mark.parametrize("query,expected_route", [
    ("Xin chào bạn!", "general"),
    ("Cho tôi tips về visa Nhật", "general"),
    ("Tôi muốn đi Đà Nẵng 3 ngày ngân sách 8 triệu", "travel"),
    ("Lên kế hoạch du lịch Phú Quốc 5 ngày", "travel"),
    ("Thời tiết Hội An như thế nào?", "travel"),
])
def test_supervisor_routing(query, expected_route):
    state = {"user_query": query, "messages": []}
    result = supervisor_node(state)
    assert result["route"] == expected_route
```

---

## Phase 5 — Graph Assembly

### T5.1 — `app/router.py` — Conditional Edge Logic
**Mô tả:** Pure function quyết định edge tiếp theo dựa trên `state["route"]`.

**Depends on:** T4.4  
**Blocks:** T5.2

```python
def route_after_supervisor(state: TravelState) -> str:
    return state.get("route", "general")
```

**Acceptance Criteria:**
- [ ] Pure function — không side effects, không LLM call
- [ ] Default `"general"` nếu `route` không có trong state

**Test Plan:**
```python
def test_router_general():
    assert route_after_supervisor({"route": "general"}) == "general"

def test_router_travel():
    assert route_after_supervisor({"route": "travel"}) == "travel"

def test_router_default():
    assert route_after_supervisor({}) == "general"
```

---

### T5.2 — `app/graph.py` — Graph Compilation
**Mô tả:** Kết nối tất cả nodes và edges thành LangGraph `StateGraph`.

**Depends on:** T4.1, T4.2, T4.3, T4.4, T5.1, T0.5  
**Blocks:** T6.1, T7.3

**Topology:**
```
START → supervisor → [router] → general_agent → END
                              → travel_knowledge → planner → END
```

**Acceptance Criteria:**
- [ ] `from app.graph import graph` không lỗi
- [ ] `graph.invoke({"user_query": "..."})` không crash
- [ ] `graph.get_graph().draw_mermaid()` hiển thị đúng 4 nodes
- [ ] General flow: `final_response` có data, `itinerary` rỗng
- [ ] Travel flow: `itinerary`, `estimated_budget`, `final_response` đều có data
- [ ] Langfuse `CallbackHandler` được inject vào mọi `graph.invoke()` call
- [ ] Trace xuất hiện trên Langfuse dashboard sau mỗi request

**Test Plan:**
```python
def test_graph_general_flow():
    result = graph.invoke({"user_query": "Xin chào!", "messages": []})
    assert result["final_response"] != ""
    assert result.get("itinerary", "") == ""

def test_graph_travel_flow():
    result = graph.invoke({
        "user_query": "Lên kế hoạch 3 ngày Đà Nẵng, ngân sách 10 triệu",
        "messages": []
    })
    assert result["itinerary"] != ""
    assert result["final_response"] != ""
```

---

## Phase 6 — UI

### T6.1 — `ui/gradio.py` — Gradio Chat Interface
**Mô tả:** Giao diện chat, streaming response, hiển thị Markdown.

**Depends on:** T5.2  
**Blocks:** T7.3

**Acceptance Criteria:**
- [ ] `python ui/gradio.py` khởi động tại `http://localhost:7860`
- [ ] Chat input/output hoạt động
- [ ] Itinerary hiển thị Markdown có format đẹp
- [ ] Lỗi từ graph được bắt, hiển thị friendly message (không traceback)

**Test Plan:** Manual — test 2 scenarios:
1. "Xin chào" → general response
2. "Lên kế hoạch 3 ngày Đà Nẵng ngân sách 10 triệu" → itinerary có format

---

## Phase 7 — Tests

### T7.1 — `tests/test_tools.py` — Tool Unit Tests
**Mô tả:** Unit test cho 5 tools với mock external APIs.

**Depends on:** T2.1, T2.2, T2.3, T2.4, T2.5  
**Blocks:** T7.3

**Acceptance Criteria:**
- [ ] Coverage tất cả 5 tools
- [ ] Mock tất cả external API
- [ ] Test happy path và error path
- [ ] `pytest tests/test_tools.py` → 100% pass

---

### T7.2 — `tests/test_agents.py` — Agent Unit Tests
**Mô tả:** Unit test 4 agents. Mock LLM và tool calls.

**Depends on:** T4.1, T4.2, T4.3, T4.4  
**Blocks:** T7.3

**Acceptance Criteria:**
- [ ] Test scope enforcement (agent không gọi tool ngoài phạm vi)
- [ ] Test state mutation đúng
- [ ] `pytest tests/test_agents.py` → 100% pass

---

### T7.3 — `tests/test_e2e.py` — End-to-End Integration Tests
**Mô tả:** Test toàn bộ graph với real API calls (cần `.env` đầy đủ).

**Depends on:** T5.2, T7.1, T7.2  
**Blocks:** _(task cuối cùng)_

**Test cases:**
1. General conversation flow
2. Travel planning flow với đủ thông tin
3. Travel planning flow thiếu ngân sách (edge case)

**Acceptance Criteria:**
- [ ] 3 test cases pass với real APIs
- [ ] Thời gian chạy ≤ 60 giây/test
- [ ] Không crash khi thiếu optional field trong state

---

## Execution Order Summary

| Wave | Tasks (song song) | Điều kiện bắt đầu |
|---|---|---|
| 0 | T0.1, T0.2, **T0.5**, T1.1, T1.2 | Ngay lập tức |
| 1 | T0.3, T0.4 | T0.1 done |
| 2 | T2.1, T2.2, T2.3, T2.4, T2.5 | T0.3+T0.4 done (T2.5 thêm T1.1) |
| 3 | T3.1 | T2.5 + T1.1 done |
| 4 | T3.2 | T3.1 done |
| 5 | T4.1, T4.2, T4.3, T4.4 | Deps tương ứng done |
| 6 | T5.1 | T4.4 done |
| 7 | T5.2 | T4.1+T4.2+T4.3+T4.4+T5.1+**T0.5** done |
| 8 | T6.1, T7.1, T7.2, T7.3 | T5.2 done (T7.1/T7.2 sớm hơn) |

**Ước tính tổng:** ~15–21 giờ làm việc thực tế.
