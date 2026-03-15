"""Search service — SearXNG web search with caching."""

import httpx
import structlog

from src.config import settings

logger = structlog.get_logger(__name__)


async def web_search(query: str, max_results: int = 5) -> list[dict]:
    """Search the web via SearXNG."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{settings.search.searxng_url}/search",
                params={
                    "q": query,
                    "format": "json",
                    "engines": "google,duckduckgo",
                    "categories": "general",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])[:max_results]
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", ""),
                }
                for r in results
            ]
    except Exception as e:
        logger.warning("web_search_failed", error=str(e), query=query)
        return []


async def search_and_summarize(query: str) -> str:
    """Search the web and return a summarized result."""
    results = await web_search(query)
    if not results:
        return "No web results found."

    combined = "\n".join(f"- {r['title']}: {r['content']}" for r in results if r["content"])
    return combined[:1500] if combined else "No relevant content found."
