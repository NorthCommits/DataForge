from __future__ import annotations

from typing import List

from loguru import logger

from ..api.tavily_client import TavilyClient
from ..types import SourceDocument


def _credibility_score(url: str) -> float:
    # Very simple heuristic by domain suffix and presence of known TLDs
    url_l = url.lower()
    if any(t in url_l for t in [".gov", ".edu"]):
        return 0.9
    if any(t in url_l for t in [".org", "medium.com", "arxiv.org", "nature.com", "acm.org"]):
        return 0.75
    if any(t in url_l for t in ["twitter.com", "x.com", "reddit.com", "youtube.com"]):
        return 0.4
    return 0.6


class TavilyScraper:
    def __init__(self) -> None:
        self._client = TavilyClient()

    async def close(self) -> None:
        await self._client.close()

    async def scrape(self, topic: str, limit: int = 10) -> List[SourceDocument]:
        logger.info("Scraping via Tavily: topic={} limit={} ", topic, limit)
        result = await self._client.search(topic, max_results=limit)
        docs: List[SourceDocument] = []
        for d in result.documents[:limit]:
            score = _credibility_score(d.url)
            d.source_score = score if d.source_score is None else (d.source_score + score) / 2.0
            docs.append(d)
        return docs
