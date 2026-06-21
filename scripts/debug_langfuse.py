"""
Debug script — kiểm tra từng bước tại sao Langfuse không nhận trace.
Chạy: python scripts/debug_langfuse.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.config import config as app_config

SEP = "-" * 60


def step(n, title):
    print(f"\n[Step {n}] {title}")
    print(SEP)


# ── Step 1: Kiểm tra keys trong .env ─────────────────────────────────────────
step(1, "Kiểm tra Langfuse keys trong .env")
pk = app_config.LANGFUSE_PUBLIC_KEY
sk = app_config.LANGFUSE_SECRET_KEY
host = app_config.LANGFUSE_HOST
print(f"  LANGFUSE_PUBLIC_KEY : {pk[:12]}... ({len(pk)} chars)" if pk else "  LANGFUSE_PUBLIC_KEY : ❌ TRỐNG")
print(f"  LANGFUSE_SECRET_KEY : {sk[:12]}... ({len(sk)} chars)" if sk else "  LANGFUSE_SECRET_KEY : ❌ TRỐNG")
print(f"  LANGFUSE_HOST       : {host}")

if not pk or not sk:
    print("\n❌ Thiếu keys. Điền LANGFUSE_PUBLIC_KEY và LANGFUSE_SECRET_KEY vào .env rồi chạy lại.")
    sys.exit(1)


# ── Step 2: Import langfuse ───────────────────────────────────────────────────
step(2, "Import langfuse package")
try:
    import langfuse
    print(f"  ✅ langfuse {langfuse.__version__} imported OK")
except ImportError as e:
    print(f"  ❌ Import failed: {e}")
    sys.exit(1)


# ── Step 3: Auth check (kết nối + xác thực key) ───────────────────────────────
step(3, "Auth check — kết nối tới Langfuse server")
try:
    from langfuse import Langfuse
    lf = Langfuse(public_key=pk, secret_key=sk, host=host)
    result = lf.auth_check()
    print(f"  ✅ Auth OK: {result}")
except Exception as e:
    print(f"  ❌ Auth failed: {e}")
    print("  Kiểm tra:")
    print("    - Docker có đang chạy không? (docker compose ps)")
    print(f"    - Có truy cập được {host} từ browser không?")
    print("    - Key có đúng không? (tạo key mới trong Langfuse dashboard)")
    sys.exit(1)


# ── Step 4: Tạo trace và gửi ─────────────────────────────────────────────────
step(4, "Tạo trace test và flush")
try:
    import uuid
    trace_id = str(uuid.uuid4())
    trace = lf.trace(
        id=trace_id,
        name="debug-test",
        user_id="debug-script",
        tags=["debug"],
    )
    lf.flush()
    print(f"  ✅ Trace tạo thành công: {trace_id}")
    print(f"  Kiểm tra trên Langfuse: {host}/traces/{trace_id}")
except Exception as e:
    print(f"  ❌ Tạo trace thất bại: {e}")
    sys.exit(1)


# ── Step 5: Test get_langchain_handler ────────────────────────────────────────
step(5, "Test trace.get_langchain_handler()")
try:
    trace2 = lf.trace(id=str(uuid.uuid4()), name="handler-test")
    handler = trace2.get_langchain_handler()
    print(f"  ✅ Handler tạo OK: {type(handler).__name__}")
    inner_client = getattr(handler, "langfuse", None)
    print(f"  handler.langfuse: {type(inner_client).__name__ if inner_client else '❌ None'}")
    if inner_client:
        inner_client.flush()
        print("  ✅ flush() OK")
except Exception as e:
    print(f"  ❌ Handler failed: {e}")
    sys.exit(1)


# ── Step 6: Test LangChain callback integration ───────────────────────────────
step(6, "Test LangChain callback với ChatOpenAI")
openai_key = app_config.OPENAI_API_KEY
if not openai_key:
    print("  ⚠️  OPENAI_API_KEY trống — bỏ qua step này")
else:
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage

        trace3 = lf.trace(id=str(uuid.uuid4()), name="llm-callback-test", tags=["debug"])
        cb_handler = trace3.get_langchain_handler()

        llm = ChatOpenAI(model=app_config.LLM_MODEL, temperature=0, openai_api_key=openai_key)
        response = llm.invoke([HumanMessage(content="Nói 'OK' bằng tiếng Việt.")],
                              config={"callbacks": [cb_handler]})
        print(f"  ✅ LLM response: {response.content[:80]}")

        cb_handler.langfuse.flush()
        print(f"  ✅ Trace ID: {trace3.id}")
        print(f"  Kiểm tra: {host}/traces/{trace3.id}")
    except Exception as e:
        print(f"  ❌ LangChain callback test failed: {e}")
        sys.exit(1)


# ── Kết quả ───────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("✅ Tất cả steps PASS — Langfuse hoạt động bình thường.")
print(f"   Dashboard: {host}")
print(f"   Nếu vẫn không thấy trace trong app, restart Streamlit.")
print('='*60)
