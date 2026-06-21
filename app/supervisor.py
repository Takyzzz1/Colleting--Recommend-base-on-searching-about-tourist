"""Supervisor node — semantic router that classifies intent and extracts travel details."""
import json
import os
import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langchain_core.runnables import RunnableConfig
from app.config import config as app_config
from app.state import TravelState

_PROMPT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", "supervisor.md")

_DEFAULT_OUTPUT = {
    "route": "general",
    "destination": "",
    "duration_days": 0,
    "budget": 0.0,
    "interests": [],
    "travel_dates": "",
    "clarification_question": "",
}


def _system_prompt() -> str:
    with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _parse_json(text: str) -> dict:
    clean = re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        return dict(_DEFAULT_OUTPUT)


def _build_history_text(messages: list[BaseMessage]) -> str:
    """Format full message history as a readable transcript for the supervisor LLM."""
    lines = []
    for m in messages:
        role = "User" if isinstance(m, HumanMessage) else "Assistant"
        content = m.content if hasattr(m, "content") else str(m)
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def supervisor_node(state: TravelState, config: RunnableConfig) -> dict:
    messages = state.get("messages", [])

    # Last human message is the current query
    user_query = ""
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            user_query = m.content if hasattr(m, "content") else str(m)
            break
    if not user_query:
        user_query = state.get("user_query", "")

    # Build full conversation transcript for history-aware extraction
    history_text = _build_history_text(messages)
    input_content = (
        f"[Toàn bộ lịch sử hội thoại]\n{history_text}\n\n"
        f"[Câu hỏi/yêu cầu hiện tại của người dùng]\n{user_query}"
    ) if len(messages) > 1 else user_query

    llm = ChatOpenAI(
        model=app_config.LLM_MODEL,
        temperature=0,
        openai_api_key=app_config.OPENAI_API_KEY,
    )
    response = llm.invoke(
        [SystemMessage(content=_system_prompt()), HumanMessage(content=input_content)],
        config=config,
    )

    parsed = _parse_json(response.content)
    result = {**_DEFAULT_OUTPUT, **parsed}

    base_updates = {
        "destination": result.get("destination", ""),
        "duration_days": int(result.get("duration_days") or 0),
        "budget": float(result.get("budget") or 0.0),
        "interests": result.get("interests") or [],
        "travel_dates": result.get("travel_dates", ""),
        "user_query": user_query,
    }

    # Clarification path: supervisor detected missing required fields
    if result["route"] == "clarify":
        question = result.get("clarification_question") or (
            "Bạn có thể cho tôi biết thêm thông tin về chuyến đi không? "
            "Tôi cần biết: điểm đến và số ngày bạn muốn đi."
        )
        return {**base_updates, "route": "clarify", "final_response": question}

    return {**base_updates, "route": result["route"]}
