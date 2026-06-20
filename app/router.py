"""Conditional edge function for LangGraph routing."""
from app.state import TravelState


def route_after_supervisor(state: TravelState) -> str:
    """Return the next node name based on route set by supervisor."""
    route = state.get("route", "general")
    if route == "travel":
        return "travel_knowledge"
    return "general"
