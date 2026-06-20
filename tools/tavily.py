"""Tavily real-time search tool with LLM-based summarization."""
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from app.config import config


@tool
def tavily_search(query: str, max_results: int = 5) -> dict:
    """Search the internet for real-time travel information. Returns a summarized result."""
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=config.TAVILY_API_KEY)
        response = client.search(query=query, max_results=max_results)
        results = response.get("results", [])
    except Exception as e:
        return {"summary": f"Không thể tìm kiếm thông tin: {str(e)}", "sources": []}

    if not results:
        return {"summary": "Không tìm thấy thông tin liên quan.", "sources": []}

    raw_text = "\n\n".join(
        f"[{r.get('title', '')}]\n{r.get('content', '')}" for r in results
    )
    sources = [r.get("url", "") for r in results if r.get("url")]

    llm = ChatOpenAI(
        model=config.LLM_MODEL,
        temperature=0,
        openai_api_key=config.OPENAI_API_KEY,
    )
    prompt = (
        f"Tóm tắt các thông tin sau đây thành một đoạn văn ngắn gọn (tối đa 400 từ) "
        f"liên quan đến câu hỏi: '{query}'. Chỉ giữ lại thông tin hữu ích nhất, "
        f"bỏ qua quảng cáo và nội dung không liên quan. Viết bằng tiếng Việt.\n\n{raw_text}"
    )
    summary = llm.invoke(prompt).content

    return {"summary": summary, "sources": sources}
