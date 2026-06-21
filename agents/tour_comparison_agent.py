"""Tour Comparison Agent — searches real tour packages and compares them."""
import json
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from app.config import config as app_config
from app.state import TravelState
from tools.tour_search import tour_search

_PROMPT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", "tour_comparison.md")


def _system_prompt() -> str:
    with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def tour_comparison_node(state: TravelState, config: RunnableConfig) -> dict:
    destination = state.get("destination", "")
    duration_days = state.get("duration_days") or 3
    budget = state.get("budget") or 0.0
    existing_itinerary = state.get("final_response", "")

    # Search for real tour packages
    search_result = tour_search.invoke({
        "destination": destination,
        "duration_days": duration_days,
        "budget": budget,
    })

    raw_results = search_result.get("results", [])
    has_results = len(raw_results) > 0

    # Format raw results for LLM
    results_text = json.dumps(raw_results, ensure_ascii=False, indent=2) if has_results else "[]"

    user_content = (
        f"Điểm đến: {destination}\n"
        f"Số ngày: {duration_days}\n"
        f"Ngân sách: {budget:,.0f} VND\n\n"
        f"Kết quả tìm kiếm tour (raw JSON):\n{results_text}"
    )

    llm = ChatOpenAI(
        model=app_config.LLM_MODEL,
        temperature=0,
        openai_api_key=app_config.OPENAI_API_KEY,
    )
    response = llm.invoke(
        [SystemMessage(content=_system_prompt()), HumanMessage(content=user_content)],
        config=config,
    )

    tour_comparison = response.content

    # Append tour comparison after the AI-generated itinerary
    separator = "\n\n---\n\n"
    combined_response = f"{existing_itinerary}{separator}{tour_comparison}" if existing_itinerary else tour_comparison

    return {
        "tour_comparison": tour_comparison,
        "final_response": combined_response,
    }
