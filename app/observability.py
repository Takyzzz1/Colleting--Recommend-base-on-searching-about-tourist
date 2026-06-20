"""Langfuse observability for LangGraph tracing (self-hosted via Docker)."""
import uuid
from typing import Optional
from app.config import config


def get_langfuse_handler(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    route_taken: Optional[str] = None,
):
    """
    Return a Langfuse CallbackHandler pointed at the self-hosted instance.
    Returns None gracefully when Langfuse keys are not configured.
    """
    if not config.LANGFUSE_PUBLIC_KEY or not config.LANGFUSE_SECRET_KEY:
        return None, None

    try:
        from langfuse.callback import CallbackHandler

        _trace_id = trace_id or str(uuid.uuid4())
        tags = [f"model-{config.LLM_MODEL}"]
        if route_taken:
            tags.append(f"route-{route_taken}")

        handler = CallbackHandler(
            public_key=config.LANGFUSE_PUBLIC_KEY,
            secret_key=config.LANGFUSE_SECRET_KEY,
            host=config.LANGFUSE_HOST,
            session_id=session_id,
            user_id=user_id or "anonymous",
            trace_id=_trace_id,
            tags=tags,
        )
        return handler, _trace_id
    except Exception:
        return None, None


def submit_feedback(trace_id: str, score: float, comment: str = "") -> bool:
    """
    Submit a user feedback score (1.0 = thumbs up, 0.0 = thumbs down)
    directly to the self-hosted Langfuse instance.
    """
    if not trace_id or not config.LANGFUSE_PUBLIC_KEY:
        return False

    try:
        from langfuse import Langfuse

        client = Langfuse(
            public_key=config.LANGFUSE_PUBLIC_KEY,
            secret_key=config.LANGFUSE_SECRET_KEY,
            host=config.LANGFUSE_HOST,
        )
        client.score(
            trace_id=trace_id,
            name="user_feedback",
            value=score,
            comment=comment or ("👍 Helpful" if score == 1.0 else "👎 Not helpful"),
        )
        client.flush()
        return True
    except Exception:
        return False
