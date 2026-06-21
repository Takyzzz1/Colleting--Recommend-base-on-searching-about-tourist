"""Travel Knowledge Agent — retrieves information via RAG and Tavily."""
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from app.config import config
from app.state import TravelState
from tools.rag import rag_search
from tools.tavily import tavily_search

_PROMPT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", "travel_knowledge.md")


def _system_prompt() -> str:
    with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def travel_knowledge_node(state: TravelState, run_config: RunnableConfig) -> dict:
    destination = state.get("destination", "")
    user_query = state.get("user_query", "")
    interests = state.get("interests", [])

    rag_query = f"{destination} {' '.join(interests)}".strip() or user_query
    tavily_query = f"du lịch {destination} {' '.join(interests)} giá cả khách sạn tour".strip()

    rag_result = rag_search.invoke({"query": rag_query, "n_results": 4})
    tavily_result = tavily_search.invoke({"query": tavily_query, "max_results": 5})

    rag_context = rag_result.get("context", "")
    tavily_context = tavily_result.get("summary", "")

    llm = ChatOpenAI(
        model=config.LLM_MODEL,
        temperature=config.LLM_TEMPERATURE,
        openai_api_key=config.OPENAI_API_KEY,
    )
    synthesis_prompt = (
        f"Người dùng hỏi: {user_query}\n\n"
        f"Thông tin từ cơ sở kiến thức nội bộ (RAG):\n{rag_context}\n\n"
        f"Thông tin thực tế từ internet (Tavily):\n{tavily_context}\n\n"
        "Hãy tổng hợp thành một bản tóm tắt có cấu trúc theo định dạng quy định trong prompt hệ thống."
    )
    response = llm.invoke(
        [SystemMessage(content=_system_prompt()), HumanMessage(content=synthesis_prompt)],
        config=run_config,
    )

    return {
        "rag_context": rag_context,
        "tavily_context": tavily_context,
        "final_response": response.content,
    }
