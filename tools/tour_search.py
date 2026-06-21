"""Tour search tool — finds real tour packages via Tavily multi-query search."""
from langchain_core.tools import tool
from app.config import config


@tool
def tour_search(destination: str, duration_days: int = 3, budget: float = 0) -> dict:
    """
    Search for real travel tour packages for a destination using multiple queries.
    Returns raw results for the agent to extract and compare.
    """
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=config.TAVILY_API_KEY)
    except Exception as e:
        return {"results": [], "error": str(e)}

    queries = [
        f"tour du lịch {destination} {duration_days} ngày trọn gói giá bao nhiêu 2025",
        f"tour {destination} giá rẻ khuyến mãi ăn ở đưa đón 2025",
    ]

    seen_urls: set[str] = set()
    all_results: list[dict] = []

    for query in queries:
        try:
            response = client.search(
                query=query,
                max_results=5,
                search_depth="advanced",
                include_domains=[
                    "vietravel.com", "saigontourist.net", "luxtravel.vn",
                    "dulichviet.com.vn", "traveloka.com", "agoda.com",
                    "vietnammice.vn", "dulichhoian.com", "booking.com",
                ],
            )
            for r in response.get("results", []):
                url = r.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_results.append({
                        "title": r.get("title", ""),
                        "url": url,
                        "content": r.get("content", "")[:800],
                        "score": r.get("score", 0),
                    })
        except Exception:
            continue

    # Sort by relevance score, cap at 10 results
    all_results.sort(key=lambda x: x["score"], reverse=True)
    return {
        "results": all_results[:10],
        "destination": destination,
        "duration_days": duration_days,
        "budget": budget,
    }
