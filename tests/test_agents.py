"""T7.2 — Agent scope enforcement tests."""
import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage


def _base_state(user_query: str = "", route: str = "general") -> dict:
    return {
        "messages": [HumanMessage(content=user_query)],
        "user_query": user_query,
        "destination": "Đà Nẵng",
        "travel_dates": "tháng 12",
        "duration_days": 3,
        "budget": 5_000_000.0,
        "interests": ["ẩm thực"],
        "rag_context": "Đà Nẵng nổi tiếng với bãi biển Mỹ Khê.",
        "tavily_context": "Khách sạn tại Đà Nẵng từ 400k/đêm.",
        "weather": {},
        "travel_distances": {},
        "estimated_budget": {},
        "itinerary": "",
        "final_response": "",
        "route": route,
    }


class TestGeneralAgent:
    @patch("agents.general_agent.ChatOpenAI")
    def test_returns_final_response(self, mock_llm_cls):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="Bạn nên mang kem chống nắng khi đi biển.")
        mock_llm_cls.return_value = mock_llm

        from agents.general_agent import general_agent_node
        result = general_agent_node(_base_state("Đi biển cần mang gì?"))

        assert "final_response" in result
        assert len(result["final_response"]) > 0

    @patch("agents.general_agent.ChatOpenAI")
    def test_does_not_set_itinerary(self, mock_llm_cls):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="Câu trả lời chung.")
        mock_llm_cls.return_value = mock_llm

        from agents.general_agent import general_agent_node
        result = general_agent_node(_base_state("Xin chào"))

        assert "itinerary" not in result, "General agent must not set itinerary"


class TestTravelKnowledgeAgent:
    @patch("agents.travel_knowledge_agent.ChatOpenAI")
    @patch("agents.travel_knowledge_agent.tavily_search")
    @patch("agents.travel_knowledge_agent.rag_search")
    def test_sets_rag_and_tavily_context(self, mock_rag, mock_tavily, mock_llm_cls):
        mock_rag.invoke.return_value = {"context": "RAG nội dung.", "sources": ["da_nang.md"]}
        mock_tavily.invoke.return_value = {"summary": "Tavily tóm tắt.", "sources": ["http://x.com"]}
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="Thông tin tổng hợp.")
        mock_llm_cls.return_value = mock_llm

        from agents.travel_knowledge_agent import travel_knowledge_node
        result = travel_knowledge_node(_base_state("Cho tôi biết về Đà Nẵng"))

        assert "rag_context" in result
        assert "tavily_context" in result
        assert result["rag_context"] != ""
        assert result["tavily_context"] != ""

    @patch("agents.travel_knowledge_agent.ChatOpenAI")
    @patch("agents.travel_knowledge_agent.tavily_search")
    @patch("agents.travel_knowledge_agent.rag_search")
    def test_does_not_generate_itinerary(self, mock_rag, mock_tavily, mock_llm_cls):
        mock_rag.invoke.return_value = {"context": "content", "sources": []}
        mock_tavily.invoke.return_value = {"summary": "summary", "sources": []}
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="Tổng quan Đà Nẵng...")
        mock_llm_cls.return_value = mock_llm

        from agents.travel_knowledge_agent import travel_knowledge_node
        result = travel_knowledge_node(_base_state("Thông tin du lịch Đà Nẵng"))

        # Knowledge agent must not set itinerary (that's planner's job)
        assert "itinerary" not in result or result.get("itinerary", "") == ""


class TestPlannerAgent:
    @patch("agents.planner_agent.ChatOpenAI")
    @patch("agents.planner_agent.calculate_budget")
    @patch("agents.planner_agent.get_distance")
    @patch("agents.planner_agent.get_weather")
    def test_sets_itinerary_and_final_response(self, mock_weather, mock_distance, mock_budget, mock_llm_cls):
        mock_weather.invoke.return_value = {"city": "Đà Nẵng", "forecast": []}
        mock_distance.invoke.return_value = {"distance_km": 20, "duration_min": 30}
        mock_budget.invoke.return_value = {"total": 4_000_000, "remaining": 1_000_000, "is_over_budget": False, "breakdown": {}, "suggestions": []}
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="### Ngày 1: Khám phá Đà Nẵng\n...")
        mock_llm_cls.return_value = mock_llm

        from agents.planner_agent import planner_agent_node
        result = planner_agent_node(_base_state("Lên lịch 3 ngày Đà Nẵng"))

        assert "itinerary" in result
        assert "final_response" in result
        assert len(result["itinerary"]) > 0

    @patch("agents.planner_agent.ChatOpenAI")
    @patch("agents.planner_agent.calculate_budget")
    @patch("agents.planner_agent.get_distance")
    @patch("agents.planner_agent.get_weather")
    def test_calls_weather_tool(self, mock_weather, mock_distance, mock_budget, mock_llm_cls):
        mock_weather.invoke.return_value = {"city": "Đà Nẵng", "forecast": []}
        mock_distance.invoke.return_value = {}
        mock_budget.invoke.return_value = {"total": 0, "remaining": 0, "is_over_budget": False, "breakdown": {}, "suggestions": []}
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="Lịch trình...")
        mock_llm_cls.return_value = mock_llm

        from agents.planner_agent import planner_agent_node
        planner_agent_node(_base_state())

        mock_weather.invoke.assert_called_once()
