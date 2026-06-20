"""Streamlit UI — Multi-Agent Travel Planning System."""
import uuid
import streamlit as st
from langchain_core.messages import HumanMessage
from app.graph import graph
from app.observability import get_langfuse_handler, submit_feedback

st.set_page_config(
    page_title="🗺️ AI Travel Planner",
    page_icon="🗺️",
    layout="wide",
)

st.title("🗺️ Multi-Agent AI Travel Planner")
st.caption("Powered by LangGraph · GPT-4o-mini · RAG + Tavily")

# ── Session state initialisation ─────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []          # list of {role, content, route, trace_id}
if "last_trace_id" not in st.session_state:
    st.session_state.last_trace_id = None
if "feedback_submitted" not in st.session_state:
    st.session_state.feedback_submitted = False

# ── Render chat history ───────────────────────────────────────────────────────
for turn in st.session_state.chat_history:
    with st.chat_message(turn["role"]):
        st.markdown(turn["content"])
        if turn["role"] == "assistant" and turn.get("route"):
            route_label = "🧭 General Agent" if turn["route"] == "general" else "🏖️ Travel Knowledge + Planner"
            st.caption(f"Route: **{route_label}**")

# ── Feedback buttons (only after last assistant turn) ─────────────────────────
if st.session_state.last_trace_id and not st.session_state.feedback_submitted:
    st.divider()
    st.write("**Phản hồi của bạn về câu trả lời vừa rồi:**")
    col1, col2, _ = st.columns([1, 1, 8])
    with col1:
        if st.button("👍 Hữu ích"):
            submit_feedback(st.session_state.last_trace_id, score=1.0)
            st.session_state.feedback_submitted = True
            st.success("Cảm ơn phản hồi của bạn!")
            st.rerun()
    with col2:
        if st.button("👎 Chưa tốt"):
            submit_feedback(st.session_state.last_trace_id, score=0.0)
            st.session_state.feedback_submitted = True
            st.warning("Cảm ơn! Chúng tôi sẽ cải thiện.")
            st.rerun()

# ── Chat input ────────────────────────────────────────────────────────────────
user_input = st.chat_input("Hỏi về du lịch hoặc yêu cầu lập kế hoạch chuyến đi...")

if user_input:
    # Render user message immediately
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.chat_history.append({"role": "user", "content": user_input, "route": None, "trace_id": None})
    st.session_state.feedback_submitted = False

    # Build trace_id for this turn
    trace_id = str(uuid.uuid4())

    # Invoke the graph
    with st.chat_message("assistant"):
        with st.spinner("Đang xử lý..."):
            thread_config = {"configurable": {"thread_id": st.session_state.session_id}}

            # Get Langfuse callback handler (no-op if not configured)
            handler, _ = get_langfuse_handler(
                session_id=st.session_state.session_id,
                user_id="streamlit_user",
                trace_id=trace_id,
            )
            run_config = {"callbacks": [handler]} if handler else {}
            run_config.update(thread_config)

            initial_state = {
                "messages": [HumanMessage(content=user_input)],
                "user_query": user_input,
                "destination": "",
                "travel_dates": "",
                "duration_days": 0,
                "budget": 0.0,
                "interests": [],
                "rag_context": "",
                "tavily_context": "",
                "weather": {},
                "travel_distances": {},
                "estimated_budget": {},
                "itinerary": "",
                "final_response": "",
                "route": "general",
            }

            try:
                result = graph.invoke(initial_state, config=run_config)
                response_text = result.get("final_response", "Xin lỗi, tôi không thể xử lý yêu cầu này.")
                route_taken = result.get("route", "general")
            except Exception as e:
                response_text = f"Đã xảy ra lỗi: {str(e)}"
                route_taken = "general"

        st.markdown(response_text)
        route_label = "🧭 General Agent" if route_taken == "general" else "🏖️ Travel Knowledge + Planner"
        st.caption(f"Route: **{route_label}**")

    # Persist to chat history
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": response_text,
        "route": route_taken,
        "trace_id": trace_id,
    })
    st.session_state.last_trace_id = trace_id
    st.rerun()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("ℹ️ Hướng dẫn")
    st.markdown("""
**Câu hỏi chung:**
- Tôi cần mang gì khi đi biển?
- Visa Việt Nam cần những giấy tờ gì?

**Lập kế hoạch chuyến đi:**
- Lên lịch 3 ngày tại Đà Nẵng, ngân sách 5 triệu
- Tôi muốn đi Hội An 2 ngày, thích ẩm thực và văn hóa
- Kế hoạch 5 ngày Hà Nội cho cặp đôi, ngân sách 10 triệu
    """)
    st.divider()
    st.caption(f"Session: `{st.session_state.session_id[:8]}...`")
    if st.button("🔄 Cuộc hội thoại mới"):
        st.session_state.chat_history = []
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.last_trace_id = None
        st.session_state.feedback_submitted = False
        st.rerun()
