"""Shared LangGraph state for the Multi-Agent Travel Planning System."""
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class TravelState(TypedDict):
    """Central state passed through all nodes in the graph."""
    messages: Annotated[list[BaseMessage], add_messages]
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
    tour_comparison: str
    final_response: str
    route: str  # "general" | "travel" | "clarify"
