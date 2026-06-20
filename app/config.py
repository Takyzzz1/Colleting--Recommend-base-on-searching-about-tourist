"""Load and validate all environment variables."""
import os
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Missing required environment variable: {key}")
    return value


def _optional(key: str, default: str = "") -> str:
    return os.getenv(key, default)


class Config:
    OPENAI_API_KEY: str = _require("OPENAI_API_KEY")
    TAVILY_API_KEY: str = _require("TAVILY_API_KEY")
    OPENWEATHERMAP_API_KEY: str = _require("OPENWEATHERMAP_API_KEY")
    GOOGLE_MAPS_API_KEY: str = _require("GOOGLE_MAPS_API_KEY")

    LLM_MODEL: str = _optional("LLM_MODEL", "gpt-4o-mini")
    LLM_TEMPERATURE: float = float(_optional("LLM_TEMPERATURE", "0"))
    CHROMA_PERSIST_DIR: str = _optional("CHROMA_PERSIST_DIR", "./vector_db")
    EMBEDDING_MODEL: str = _optional(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )

    # Langfuse is optional — graceful degradation if not configured
    LANGFUSE_PUBLIC_KEY: str = _optional("LANGFUSE_PUBLIC_KEY")
    LANGFUSE_SECRET_KEY: str = _optional("LANGFUSE_SECRET_KEY")
    LANGFUSE_HOST: str = _optional("LANGFUSE_HOST", "https://cloud.langfuse.com")


config = Config()
