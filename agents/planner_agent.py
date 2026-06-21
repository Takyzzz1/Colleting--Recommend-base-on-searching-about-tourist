"""Planner Agent — generates full itinerary using weather, maps, and budget tools."""
import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from app.config import config
from app.state import TravelState
from tools.weather import get_weather
from tools.maps import get_distance
from tools.budget import calculate_budget

_PROMPT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", "planner.md")

# Representative attraction pairs for distance calculation per destination
_DISTANCE_PAIRS: dict[str, list[tuple[str, str]]] = {
    "đà nẵng": [("Sân bay Đà Nẵng", "Cầu Rồng"), ("Cầu Rồng", "Bán đảo Sơn Trà"), ("Bà Nà Hills", "Trung tâm Đà Nẵng")],
    "hội an": [("Đà Nẵng", "Hội An"), ("Phố cổ Hội An", "Cù Lao Chàm"), ("Hội An", "Mỹ Sơn")],
    "hà nội": [("Sân bay Nội Bài", "Hồ Hoàn Kiếm"), ("Hồ Hoàn Kiếm", "Văn Miếu"), ("Hồ Tây", "Lăng Bác")],
    "đà lạt": [("Sân bay Liên Khương", "Hồ Xuân Hương"), ("Hồ Xuân Hương", "Thung lũng Tình yêu"), ("Vườn hoa Đà Lạt", "Trung tâm Đà Lạt")],
    "phú quốc": [("Sân bay Phú Quốc", "Bãi Sao"), ("Bãi Sao", "Cáp treo Hòn Thơm"), ("Dinh Cậu", "Bãi Dài")],
    "hồ chí minh": [("Sân bay Tân Sơn Nhất", "Dinh Độc Lập"), ("Dinh Độc Lập", "Chợ Bến Thành"), ("Bảo tàng Chiến tranh", "Chùa Ngọc Hoàng")],
}


def _system_prompt() -> str:
    with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _get_distance_pairs(destination: str) -> list[dict]:
    dest_lower = destination.lower()
    for key, pairs in _DISTANCE_PAIRS.items():
        if key in dest_lower or dest_lower in key:
            results = []
            for origin, dest in pairs:
                try:
                    result = get_distance.invoke({"origin": origin, "destination": dest, "mode": "driving"})
                    results.append(result)
                except Exception:
                    pass
            return results
    return []


def planner_agent_node(state: TravelState, run_config: RunnableConfig) -> dict:
    destination = state.get("destination", "")
    travel_dates = state.get("travel_dates", "")
    duration_days = state.get("duration_days") or 3
    budget = state.get("budget") or 0.0
    interests = state.get("interests", [])
    rag_context = state.get("rag_context", "")
    tavily_context = state.get("tavily_context", "")

    # Step 1: Weather
    weather_data: dict = {}
    if destination:
        try:
            weather_data = get_weather.invoke({"city": destination, "days": min(duration_days, 5)})
        except Exception as e:
            weather_data = {"error": str(e)}

    # Step 2: Distances
    distance_data = _get_distance_pairs(destination)

    # Step 3: Rough budget estimate (mid-range defaults if not provided)
    hotel_per_night = 600_000.0
    food_per_day = 300_000.0
    estimated_budget_result: dict = {}
    if budget > 0:
        try:
            estimated_budget_result = calculate_budget.invoke({
                "hotel_per_night": hotel_per_night,
                "nights": duration_days,
                "flights": budget * 0.25,
                "food_per_day": food_per_day,
                "activities": budget * 0.15,
                "transport": budget * 0.05,
                "shopping": budget * 0.10,
                "total_budget": budget,
            })
        except Exception as e:
            estimated_budget_result = {"error": str(e)}

    # Step 4: Generate itinerary via LLM
    context_block = (
        f"## Thông tin điểm đến\n{rag_context}\n\n"
        f"## Giá cả & Thông tin hiện tại\n{tavily_context}\n\n"
        f"## Dữ liệu thời tiết\n{json.dumps(weather_data, ensure_ascii=False)}\n\n"
        f"## Khoảng cách di chuyển\n{json.dumps(distance_data, ensure_ascii=False)}\n\n"
        f"## Ước tính ngân sách\n{json.dumps(estimated_budget_result, ensure_ascii=False)}"
    )
    planning_request = (
        f"Lập lịch trình {duration_days} ngày tại {destination}.\n"
        f"Ngày đi: {travel_dates or 'chưa xác định'}\n"
        f"Ngân sách: {budget:,.0f} VND\n"
        f"Sở thích: {', '.join(interests) if interests else 'không giới hạn'}\n\n"
        f"{context_block}"
    )

    llm = ChatOpenAI(
        model=config.LLM_MODEL,
        temperature=config.LLM_TEMPERATURE,
        openai_api_key=config.OPENAI_API_KEY,
    )
    response = llm.invoke(
        [SystemMessage(content=_system_prompt()), HumanMessage(content=planning_request)],
        config=run_config,
    )

    return {
        "weather": weather_data,
        "travel_distances": {"segments": distance_data},
        "estimated_budget": estimated_budget_result,
        "itinerary": response.content,
        "final_response": response.content,
    }
