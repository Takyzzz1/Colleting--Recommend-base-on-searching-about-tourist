"""
T7.0 — Routing tests (Lab 3 requirement: ≥6 routing scenarios).
Tests that the supervisor correctly classifies intent without real LLM calls.
"""
import json
import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage


def _make_supervisor_response(route: str, destination: str = "", duration_days: int = 0,
                               budget: float = 0.0, interests: list = None, travel_dates: str = "") -> MagicMock:
    """Create a mock LLM response for supervisor_node."""
    payload = {
        "route": route,
        "destination": destination,
        "duration_days": duration_days,
        "budget": budget,
        "interests": interests or [],
        "travel_dates": travel_dates,
    }
    mock = MagicMock()
    mock.content = json.dumps(payload)
    return mock


def _make_state(user_message: str) -> dict:
    return {
        "messages": [HumanMessage(content=user_message)],
        "user_query": user_message,
        "destination": "",
        "travel_dates": "",
        "duration_days": 0,
        "budget": 0.0,
        "interests": [],
        "rag_context": "",
        "tavily_context": "",
        "weather": {},
        "travel_distances": {},
        "estimated_budget": {},
        "itinerary": "",
        "final_response": "",
        "route": "general",
    }


# ── Test 1: Greeting → general ─────────────────────────────────────────────
@patch("agents.general_agent.ChatOpenAI")
@patch("app.supervisor.ChatOpenAI")
def test_routing_greeting_to_general(mock_supervisor_llm, mock_general_llm):
    from app.supervisor import supervisor_node
    from app.router import route_after_supervisor

    mock_supervisor_llm.return_value.invoke.return_value = _make_supervisor_response("general")

    state = _make_state("Xin chào!")
    result = supervisor_node(state)

    assert result["route"] == "general"
    assert route_after_supervisor({**state, **result}) == "general"


# ── Test 2: Trip planning request → travel ────────────────────────────────
@patch("app.supervisor.ChatOpenAI")
def test_routing_trip_plan_to_travel(mock_llm):
    from app.supervisor import supervisor_node
    from app.router import route_after_supervisor

    mock_llm.return_value.invoke.return_value = _make_supervisor_response(
        "travel", destination="Đà Nẵng", duration_days=3, budget=5_000_000
    )

    state = _make_state("Lên kế hoạch 3 ngày tại Đà Nẵng, ngân sách 5 triệu")
    result = supervisor_node(state)

    assert result["route"] == "travel"
    assert result["destination"] == "Đà Nẵng"
    assert result["duration_days"] == 3
    assert result["budget"] == 5_000_000.0
    assert route_after_supervisor({**state, **result}) == "travel_knowledge"


# ── Test 3: General travel tip (no destination) → general ─────────────────
@patch("app.supervisor.ChatOpenAI")
def test_routing_general_tip_to_general(mock_llm):
    from app.supervisor import supervisor_node

    mock_llm.return_value.invoke.return_value = _make_supervisor_response("general")

    state = _make_state("Khi đi biển cần mang theo những gì?")
    result = supervisor_node(state)

    assert result["route"] == "general"


# ── Test 4: Itinerary request with interests → travel + interests extracted ─
@patch("app.supervisor.ChatOpenAI")
def test_routing_extracts_interests(mock_llm):
    from app.supervisor import supervisor_node

    mock_llm.return_value.invoke.return_value = _make_supervisor_response(
        "travel",
        destination="Hội An",
        duration_days=2,
        interests=["ẩm thực", "văn hóa"],
    )

    state = _make_state("Tôi muốn đi Hội An 2 ngày, thích ẩm thực và văn hóa")
    result = supervisor_node(state)

    assert result["route"] == "travel"
    assert "ẩm thực" in result["interests"]
    assert "văn hóa" in result["interests"]
    assert result["destination"] == "Hội An"


# ── Test 5: Visa question (general context) → general ─────────────────────
@patch("app.supervisor.ChatOpenAI")
def test_routing_visa_question_to_general(mock_llm):
    from app.supervisor import supervisor_node

    mock_llm.return_value.invoke.return_value = _make_supervisor_response("general")

    state = _make_state("Visa đi Việt Nam cần những giấy tờ gì?")
    result = supervisor_node(state)

    assert result["route"] == "general"


# ── Test 6: Weather + trip context → travel ───────────────────────────────
@patch("app.supervisor.ChatOpenAI")
def test_routing_weather_with_trip_context_to_travel(mock_llm):
    from app.supervisor import supervisor_node

    mock_llm.return_value.invoke.return_value = _make_supervisor_response(
        "travel", destination="Phú Quốc", duration_days=4, travel_dates="tháng 12"
    )

    state = _make_state("Tháng 12 đi Phú Quốc 4 ngày thời tiết có ổn không?")
    result = supervisor_node(state)

    assert result["route"] == "travel"
    assert result["destination"] == "Phú Quốc"
    assert result["travel_dates"] == "tháng 12"


# ── Test 7: Malformed LLM JSON → defaults to general ─────────────────────
@patch("app.supervisor.ChatOpenAI")
def test_routing_malformed_json_defaults_to_general(mock_llm):
    from app.supervisor import supervisor_node

    bad_response = MagicMock()
    bad_response.content = "Tôi không biết"  # not JSON
    mock_llm.return_value.invoke.return_value = bad_response

    state = _make_state("Hãy giúp tôi đi du lịch")
    result = supervisor_node(state)

    assert result["route"] == "general"


# ── Test 8: Budget extraction ─────────────────────────────────────────────
@patch("app.supervisor.ChatOpenAI")
def test_routing_extracts_budget(mock_llm):
    from app.supervisor import supervisor_node

    mock_llm.return_value.invoke.return_value = _make_supervisor_response(
        "travel", destination="Hà Nội", duration_days=5, budget=10_000_000
    )

    state = _make_state("Lên kế hoạch 5 ngày Hà Nội cho cặp đôi, ngân sách 10 triệu")
    result = supervisor_node(state)

    assert result["budget"] == 10_000_000.0
    assert result["route"] == "travel"
