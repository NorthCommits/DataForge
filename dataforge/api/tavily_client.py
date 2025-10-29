from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from loguru import logger

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
        
        # Validate API key
        if not self._api_key or not self._api_key.strip():
            raise TavilyAPIError("Tavily API key is missing or empty. Please check your .env file and config.yaml")
        
        # Validate max_results (Tavily typically limits to 20-100 results per request)
        requested_max = max_results or settings.api.tavily.max_results
        if requested_max > 100:
            logger.warning(
                f"max_results={requested_max} exceeds Tavily API limit. Capping to 100."
            )
        
        payload: Dict[str, Any] = {
            "api_key": self._api_key,
            "query": query,
            "max_results": min(requested_max, 100),
            "search_depth": settings.api.tavily.search_depth,
        }
        
        # Only include domains if they are non-empty
        include = include_domains or settings.api.tavily.include_domains
        if include:
            payload["include_domains"] = include
            
        exclude = exclude_domains or settings.api.tavily.exclude_domains
        if exclude:
            payload["exclude_domains"] = exclude
        
        headers = {"Content-Type": "application/json"}
        logger.debug(f"Tavily API request: query='{query}', max_results={payload['max_results']}, search_depth={payload['search_depth']}")
        
        try:
            resp = await self._client.post(TAVILY_BASE_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        except httpx.RequestError as exc:
            raise TavilyAPIError(f"HTTP error: {exc}") from exc
        except httpx.HTTPStatusError as exc:
            # Extract error message from response if available
            error_msg = f"Bad status: {exc.response.status_code}"
            
            # Try to get error details from response
            try:
                error_body = exc.response.json()
                logger.error(f"Tavily API error response: {error_body}")
                
                if isinstance(error_body, dict):
                    if "error" in error_body:
                        error_msg += f" - {error_body['error']}"
                    elif "message" in error_body:
                        error_msg += f" - {error_body['message']}"
                    elif "detail" in error_body:
                        error_msg += f" - {error_body['detail']}"
                    else:
                        # Include full response if no standard error field
                        error_msg += f" - Response: {str(error_body)[:300]}"
                else:
                    error_msg += f" - Response: {str(error_body)[:300]}"
            except Exception as json_err:
                # If JSON parsing fails, try to get text
                try:
                    error_text = exc.response.text
                    if error_text:
                        logger.error(f"Tavily API error text: {error_text[:500]}")
                        error_msg += f" - {error_text[:300]}"
                except Exception as text_err:
                    logger.error(f"Failed to extract error message: {json_err}, {text_err}")
                    pass
            
            raise TavilyAPIError(error_msg) from exc

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
