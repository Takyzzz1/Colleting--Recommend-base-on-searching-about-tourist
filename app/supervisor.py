"""Supervisor node — semantic router that classifies intent and extracts travel details."""
import json
import os
import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import config
from app.state import TravelState

_PROMPT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", "supervisor.md")

_DEFAULT_OUTPUT = {
    "route": "general",
    "destination": "",
    "duration_days": 0,
    "budget": 0.0,
    "interests": [],
    "travel_dates": "",
}


def _system_prompt() -> str:
    with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _parse_json(text: str) -> dict:
    """Extract JSON from LLM response, handling markdown code fences."""
    # Strip markdown code fences
    clean = re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        return dict(_DEFAULT_OUTPUT)


def supervisor_node(state: TravelState) -> dict:
    # Get the latest user message as the query to classify
    messages = state.get("messages", [])
    if messages:
        last_msg = messages[-1]
        user_query = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
    else:
        user_query = state.get("user_query", "")

    llm = ChatOpenAI(
        model=config.LLM_MODEL,
        temperature=0,  # deterministic routing
        openai_api_key=config.OPENAI_API_KEY,
    )
    response = llm.invoke([
        SystemMessage(content=_system_prompt()),
        HumanMessage(content=user_query),
    ])

    parsed = _parse_json(response.content)

    # Merge with defaults to ensure all keys are present
    result = {**_DEFAULT_OUTPUT, **parsed}

    return {
        "route": result["route"],
        "destination": result.get("destination", ""),
        "duration_days": int(result.get("duration_days") or 0),
        "budget": float(result.get("budget") or 0.0),
        "interests": result.get("interests") or [],
        "travel_dates": result.get("travel_dates", ""),
        "user_query": user_query,
    }
