"""General agent — LLM only, no tools. Handles greetings and general travel questions."""
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from app.config import config as app_config
from app.state import TravelState

_PROMPT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", "general.md")


def _system_prompt() -> str:
    with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def general_agent_node(state: TravelState, config: RunnableConfig) -> dict:
    llm = ChatOpenAI(
        model=app_config.LLM_MODEL,
        temperature=app_config.LLM_TEMPERATURE,
        openai_api_key=app_config.OPENAI_API_KEY,
    )
    user_query = state.get("user_query") or ""
    response = llm.invoke(
        [SystemMessage(content=_system_prompt()), HumanMessage(content=user_query)],
        config=config,
    )
    return {"final_response": response.content}
