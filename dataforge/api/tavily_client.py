from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from ..config import get_settings
from ..exceptions import TavilyAPIError, CostLimitExceededError
from ..types import SourceDocument, TavilySearchResult
from .base import BaseAPIClient
from .rate_limiter import TokenBucketRateLimiter
from ..storage.api_cache import APICache
from .cost_tracker_singleton import get_cost_tracker


TAVILY_BASE_URL = "https://api.tavily.com/search"


class TavilyClient(BaseAPIClient):
    def __init__(self, api_key: Optional[str] = None, rate_limiter: Optional[TokenBucketRateLimiter] = None) -> None:
        settings = get_settings()
        key = api_key or settings.api.tavily.api_key
        super().__init__(key)
        self._client = httpx.AsyncClient(timeout=settings.api.tavily.timeout)
        self._rate = rate_limiter or TokenBucketRateLimiter(settings.api.rate_limiting.tavily_rpm)
        self._cache = APICache()

    async def close(self) -> None:
        await self._client.aclose()

    async def search(self, query: str, max_results: Optional[int] = None, include_domains: Optional[List[str]] = None, exclude_domains: Optional[List[str]] = None) -> TavilySearchResult:
        settings = get_settings()
        await self._rate.acquire()
        # Cache key
        cache_key = f"q={query}|max={max_results or settings.api.tavily.max_results}|inc={','.join(include_domains or [])}|exc={','.join(exclude_domains or [])}"
        cached = await self._cache.get("tavily", cache_key)
        if cached is not None:
            documents: List[SourceDocument] = [
                SourceDocument(**doc) for doc in cached.get("documents", [])
            ]
            return TavilySearchResult(query=query, documents=documents, total_results=len(documents))
        payload: Dict[str, Any] = {
            "api_key": self._api_key,
            "query": query,
            "max_results": max_results or settings.api.tavily.max_results,
            "search_depth": settings.api.tavily.search_depth,
            "include_domains": include_domains or settings.api.tavily.include_domains,
            "exclude_domains": exclude_domains or settings.api.tavily.exclude_domains,
        }
        headers = {"Content-Type": "application/json"}
        try:
            resp = await self._client.post(TAVILY_BASE_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        except httpx.RequestError as exc:
            raise TavilyAPIError(f"HTTP error: {exc}") from exc
        except httpx.HTTPStatusError as exc:
            raise TavilyAPIError(f"Bad status: {exc.response.status_code}") from exc

        documents: List[SourceDocument] = []
        for item in data.get("results", []):
            documents.append(
                SourceDocument(
                    url=item.get("url", ""),
                    title=item.get("title"),
                    content=item.get("content"),
                    published_at=item.get("published_date"),
                    source_score=item.get("score"),
                )
            )
        # Persist cache
        await self._cache.set(
            "tavily",
            cache_key,
            {
                "documents": [d.model_dump() for d in documents],
            },
        )

        # Tavily pricing (placeholder flat estimate, $0 for search API if on free/dev tier)
        cost_estimate = 0.0
        tracker = get_cost_tracker()
        if not await tracker.within_budget(cost_estimate):
            raise CostLimitExceededError("Daily budget exceeded")
        await tracker.add_cost("tavily", cost_estimate)

        return TavilySearchResult(query=query, documents=documents, total_results=len(documents))
