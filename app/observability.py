"""Langfuse observability — compatible with langfuse >= 4.x."""
import uuid
import logging
from typing import Optional
from app.config import config as app_config

logger = logging.getLogger(__name__)


def check_langfuse() -> tuple[bool, str]:
    """Verify Langfuse keys and server connectivity. Returns (ok, message)."""
    if not app_config.LANGFUSE_PUBLIC_KEY or not app_config.LANGFUSE_SECRET_KEY:
        return False, "Keys not set (LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY)"
    try:
        from langfuse import Langfuse
        lf = Langfuse(
            public_key=app_config.LANGFUSE_PUBLIC_KEY,
            secret_key=app_config.LANGFUSE_SECRET_KEY,
            host=app_config.LANGFUSE_HOST,
        )
        lf.auth_check()
        return True, f"Connected → {app_config.LANGFUSE_HOST}"
    except Exception as e:
        return False, str(e)


def get_langfuse_handler(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    route_taken: Optional[str] = None,
):
    """
    Return a LangChain CallbackHandler for langfuse 4.x.
    Keys are read from env vars (LANGFUSE_PUBLIC_KEY / SECRET_KEY / HOST).
    Returns (handler, trace_id) or (None, None) if not configured.
    """
    if not app_config.LANGFUSE_PUBLIC_KEY or not app_config.LANGFUSE_SECRET_KEY:
        return None, None

    try:
        import os
        # langfuse 4.x reads these env vars internally
        os.environ.setdefault("LANGFUSE_PUBLIC_KEY", app_config.LANGFUSE_PUBLIC_KEY)
        os.environ.setdefault("LANGFUSE_SECRET_KEY", app_config.LANGFUSE_SECRET_KEY)
        os.environ.setdefault("LANGFUSE_HOST", app_config.LANGFUSE_HOST)

        from langfuse.langchain import CallbackHandler

        _trace_id = trace_id or uuid.uuid4().hex
        handler = CallbackHandler(
            public_key=app_config.LANGFUSE_PUBLIC_KEY,
            trace_context={"trace_id": _trace_id},
        )
        return handler, _trace_id
    except Exception as e:
        logger.warning("Langfuse handler creation failed: %s", e)
        return None, None


def flush_handler(handler) -> None:
    """Flush pending Langfuse events. Safe to call with None."""
    if handler is None:
        return
    try:
        from langfuse import get_client
        get_client().flush()
    except Exception as e:
        logger.debug("Langfuse flush failed: %s", e)


def submit_feedback(trace_id: str, score: float, comment: str = "") -> bool:
    """Submit 1.0 (👍) or 0.0 (👎) feedback for a trace."""
    if not trace_id or not app_config.LANGFUSE_PUBLIC_KEY:
        return False
    try:
        from langfuse import get_client
        client = get_client()
        client.create_score(
            trace_id=trace_id,
            name="user_feedback",
            value=score,
            comment=comment or ("👍 Helpful" if score == 1.0 else "👎 Not helpful"),
        )
        client.flush()
        return True
    except Exception as e:
        logger.warning("Langfuse submit_feedback failed: %s", e)
        return False
