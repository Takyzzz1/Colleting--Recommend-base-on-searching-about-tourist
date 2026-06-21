"""Conditional edge functions for LangGraph routing."""
from app.state import TravelState


def route_after_supervisor(state: TravelState) -> str:
    """Route to travel_knowledge, general, or end early with a clarification question."""
    route = state.get("route", "general")
    if route == "travel":
        return "travel_knowledge"
    if route == "clarify":
        return "__end__"
    return "general"


def route_after_knowledge(state: TravelState) -> str:
    """
    After the Knowledge Agent, only run the Planner when the user
    explicitly asked for a trip plan (duration_days > 0).
    Otherwise return the knowledge summary directly.
    """
    if state.get("duration_days", 0) > 0:
        return "planner"
    return "__end__"
