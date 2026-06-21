"""LangGraph StateGraph assembly with MemorySaver checkpointing."""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.state import TravelState
from app.supervisor import supervisor_node
from app.router import route_after_supervisor, route_after_knowledge
from agents.general_agent import general_agent_node
from agents.travel_knowledge_agent import travel_knowledge_node
from agents.planner_agent import planner_agent_node


def build_graph():
    """Build and compile the multi-agent travel planning graph."""
    builder = StateGraph(TravelState)

    builder.add_node("supervisor", supervisor_node)
    builder.add_node("general", general_agent_node)
    builder.add_node("travel_knowledge", travel_knowledge_node)
    builder.add_node("planner", planner_agent_node)

    builder.set_entry_point("supervisor")

    builder.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "general": "general",
            "travel_knowledge": "travel_knowledge",
        },
    )

    builder.add_edge("general", END)
    builder.add_conditional_edges(
        "travel_knowledge",
        route_after_knowledge,
        {
            "planner": "planner",
            "__end__": END,
        },
    )
    builder.add_edge("planner", END)

    memory = MemorySaver()
    return builder.compile(checkpointer=memory)


# Singleton — imported by the UI layer
graph = build_graph()
