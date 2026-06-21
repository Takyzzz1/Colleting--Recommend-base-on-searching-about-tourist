"""Langfuse observability for LangGraph tracing (self-hosted via Docker)."""
import uuid
import logging
from typing import Optional
from app.config import config as app_config

logger = logging.getLogger(__name__)


def check_langfuse() -> tuple[bool, str]:
    """
    Verify Langfuse connection. Returns (ok, message).
    Call this at startup or from the sidebar to diagnose issues.
    """
    if not app_config.LANGFUSE_PUBLIC_KEY or not app_config.LANGFUSE_SECRET_KEY:
        return False, "Keys not set in .env (LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY)"
    try:
        from langfuse import Langfuse
        lf = Langfuse(
            public_key=app_config.LANGFUSE_PUBLIC_KEY,
            secret_key=app_config.LANGFUSE_SECRET_KEY,
            host=app_config.LANGFUSE_HOST,
        )
        lf.auth_check()
        return True, f"Connected to {app_config.LANGFUSE_HOST}"
    except Exception as e:
        return False, str(e)


def get_langfuse_handler(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    route_taken: Optional[str] = None,
):
    """
    Create a Langfuse trace and return its LangChain CallbackHandler.
    Uses the langfuse 2.x API: Langfuse.trace() → trace.get_langchain_handler().
    Returns (None, None) gracefully when keys are not configured.
    """
    if not app_config.LANGFUSE_PUBLIC_KEY or not app_config.LANGFUSE_SECRET_KEY:
        return None, None

    try:
        from langfuse import Langfuse

        _trace_id = trace_id or str(uuid.uuid4())
        tags = [f"model-{app_config.LLM_MODEL}"]
        if route_taken:
            tags.append(f"route-{route_taken}")

        lf = Langfuse(
            public_key=app_config.LANGFUSE_PUBLIC_KEY,
            secret_key=app_config.LANGFUSE_SECRET_KEY,
            host=app_config.LANGFUSE_HOST,
        )
        trace = lf.trace(
            id=_trace_id,
            session_id=session_id,
            user_id=user_id or "anonymous",
            tags=tags,
        )
        handler = trace.get_langchain_handler()
        return handler, _trace_id
    except Exception as e:
        logger.warning("Langfuse handler creation failed: %s", e)
        return None, None


def flush_handler(handler) -> None:
    """Flush pending Langfuse events. Safe to call even if handler is None."""
    if handler is None:
        return
    try:
        # langfuse 2.x: handler has a .langfuse attribute (the underlying client)
        client = getattr(handler, "langfuse", None)
        if client is not None:
            client.flush()
    except Exception:
        pass


def submit_feedback(trace_id: str, score: float, comment: str = "") -> bool:
    """Submit 1.0 (👍) or 0.0 (👎) feedback to Langfuse for a given trace."""
    if not trace_id or not app_config.LANGFUSE_PUBLIC_KEY:
        return False

    try:
        from langfuse import Langfuse

        client = Langfuse(
            public_key=app_config.LANGFUSE_PUBLIC_KEY,
            secret_key=app_config.LANGFUSE_SECRET_KEY,
            host=app_config.LANGFUSE_HOST,
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
