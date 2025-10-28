from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List

from ..scrapers.tavily_scraper import TavilyScraper
from ..types import SourceDocument


def _sanitize_topic(topic: str) -> str:
    safe = [c if c.isalnum() or c in ("-", "_") else "_" for c in topic.strip().lower()]
    s = "".join(safe).strip("_")
    return s or "topic"


async def scrape_tavily_to_jsonl(topic: str, limit: int = 10, out_dir: Path | None = None) -> Path:
    out_base = Path("data/raw") if out_dir is None else out_dir
    out_base.mkdir(parents=True, exist_ok=True)
    date_stamp = datetime.now().strftime("%Y-%m-%d")
    filename = f"tavily_{_sanitize_topic(topic)}_{date_stamp}.jsonl"
    out_path = out_base / filename

    scraper = TavilyScraper()
    try:
        docs: List[SourceDocument] = await scraper.scrape(topic, limit)
        with out_path.open("w", encoding="utf-8") as f:
            for d in docs:
                record = {
                    "url": d.url,
                    "title": d.title,
                    "content": d.content,
                    "score": d.source_score,
                    "scraped_at": datetime.now().isoformat(),
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
    finally:
        await scraper.close()

    return out_path


