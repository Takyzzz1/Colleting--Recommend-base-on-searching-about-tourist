"""T7.1 — Unit tests for the 5 LangChain tools."""
import pytest
from unittest.mock import MagicMock, patch


# ── Budget tool (pure — no mocks needed) ──────────────────────────────────
class TestCalculateBudget:
    def test_within_budget(self):
        from tools.budget import calculate_budget
        result = calculate_budget.invoke({
            "hotel_per_night": 500_000,
            "nights": 3,
            "flights": 2_000_000,
            "food_per_day": 200_000,
            "activities": 500_000,
            "transport": 300_000,
            "shopping": 200_000,
            "total_budget": 6_000_000,
        })
        assert result["is_over_budget"] is False
        assert result["remaining"] >= 0
        assert "hotel" in result["breakdown"]

    def test_over_budget_produces_suggestions(self):
        from tools.budget import calculate_budget
        result = calculate_budget.invoke({
            "hotel_per_night": 1_000_000,
            "nights": 5,
            "flights": 5_000_000,
            "food_per_day": 500_000,
            "activities": 2_000_000,
            "transport": 500_000,
            "shopping": 1_000_000,
            "total_budget": 3_000_000,
        })
        assert result["is_over_budget"] is True
        assert len(result["suggestions"]) > 0

    def test_breakdown_keys_present(self):
        from tools.budget import calculate_budget
        result = calculate_budget.invoke({
            "hotel_per_night": 600_000,
            "nights": 2,
            "flights": 0,
            "food_per_day": 300_000,
            "activities": 0,
            "transport": 0,
            "shopping": 0,
            "total_budget": 10_000_000,
        })
        for key in ("hotel", "flights", "food", "activities", "transport", "shopping"):
            assert key in result["breakdown"]


# ── Weather tool ──────────────────────────────────────────────────────────
class TestGetWeather:
    @patch("tools.weather.requests.get")
    def test_returns_forecast(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "list": [
                {
                    "dt_txt": "2024-12-01 12:00:00",
                    "main": {"temp_min": 20.0, "temp_max": 28.0},
                    "weather": [{"description": "ít mây"}],
                    "rain": {"3h": 0.5},
                }
            ]
        }
        mock_get.return_value = mock_resp

        from tools.weather import get_weather
        result = get_weather.invoke({"city": "Da Nang", "days": 1})

        assert result["city"] == "Da Nang"
        assert len(result["forecast"]) == 1
        assert result["forecast"][0]["date"] == "2024-12-01"

    @patch("tools.weather.requests.get")
    def test_raises_on_404(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp

        from tools.weather import get_weather
        with pytest.raises(ValueError, match="City not found"):
            get_weather.invoke({"city": "NonExistentCity123"})


# ── Tavily tool ───────────────────────────────────────────────────────────
class TestTavilySearch:
    @patch("tools.tavily.ChatOpenAI")
    @patch("tools.tavily.TavilyClient")
    def test_returns_summary_and_sources(self, mock_tavily_cls, mock_llm_cls):
        mock_client = MagicMock()
        mock_client.search.return_value = {
            "results": [
                {"title": "Da Nang Guide", "content": "Beautiful beaches...", "url": "https://example.com"}
            ]
        }
        mock_tavily_cls.return_value = mock_client

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="Tóm tắt: Đà Nẵng có bãi biển đẹp.")
        mock_llm_cls.return_value = mock_llm

        from tools.tavily import tavily_search
        result = tavily_search.invoke({"query": "du lịch Đà Nẵng", "max_results": 1})

        assert "summary" in result
        assert "sources" in result
        assert len(result["sources"]) > 0

    @patch("tools.tavily.TavilyClient")
    def test_empty_results_returns_gracefully(self, mock_tavily_cls):
        mock_client = MagicMock()
        mock_client.search.return_value = {"results": []}
        mock_tavily_cls.return_value = mock_client

        from tools.tavily import tavily_search
        result = tavily_search.invoke({"query": "xyz"})
        assert result["summary"] != ""
        assert isinstance(result["sources"], list)


# ── Maps tool ─────────────────────────────────────────────────────────────
class TestGetDistance:
    @patch("tools.maps.googlemaps.Client")
    def test_returns_distance(self, mock_gmaps_cls):
        mock_gmaps = MagicMock()
        mock_gmaps.distance_matrix.return_value = {
            "rows": [{"elements": [{"status": "OK",
                                     "distance": {"value": 20000, "text": "20 km"},
                                     "duration": {"value": 1800, "text": "30 phút"}}]}]
        }
        mock_gmaps_cls.return_value = mock_gmaps

        from tools.maps import get_distance
        result = get_distance.invoke({"origin": "Đà Nẵng", "destination": "Hội An"})

        assert result["distance_km"] == 20.0
        assert result["duration_min"] == 30

    @patch("tools.maps.googlemaps.Client")
    def test_raises_on_zero_results(self, mock_gmaps_cls):
        mock_gmaps = MagicMock()
        mock_gmaps.distance_matrix.return_value = {
            "rows": [{"elements": [{"status": "ZERO_RESULTS"}]}]
        }
        mock_gmaps_cls.return_value = mock_gmaps

        from tools.maps import get_distance
        with pytest.raises(ValueError, match="No route found"):
            get_distance.invoke({"origin": "A", "destination": "B"})


# ── RAG tool ──────────────────────────────────────────────────────────────
class TestRagSearch:
    def test_empty_collection_returns_empty(self):
        """When collection is empty or doesn't exist, return gracefully."""
        with patch("tools.rag._get_collection", return_value=None):
            from tools.rag import rag_search
            result = rag_search.invoke({"query": "Đà Nẵng", "n_results": 3})
            assert result["context"] == ""
            assert result["sources"] == []

    def test_returns_context_and_sources(self):
        mock_collection = MagicMock()
        mock_collection.count.return_value = 5
        mock_collection.query.return_value = {
            "documents": [["Đà Nẵng là thành phố biển...", "Bãi biển Mỹ Khê..."]],
            "metadatas": [[{"source_file": "da_nang.md"}, {"source_file": "da_nang.md"}]],
        }
        with patch("tools.rag._get_collection", return_value=mock_collection):
            from tools.rag import rag_search
            result = rag_search.invoke({"query": "bãi biển Đà Nẵng"})
            assert len(result["context"]) > 0
            assert "da_nang.md" in result["sources"]
