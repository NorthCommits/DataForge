from __future__ import annotations

import asyncio
from pathlib import Path
from datetime import datetime
import json

import click
from dotenv import load_dotenv

from ..config import get_settings
from ..logger import setup_logger
from ..exceptions import InvalidAPIKeyError


@click.group()
def cli() -> None:
    """DataForge CLI."""


@cli.command()
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=Path("config.yaml"))
def validate_keys(config_path: Path) -> None:
    """Validate required API keys are available."""
    load_dotenv()
    setup_logger()
    settings = get_settings(config_path)

    tavily = settings.api.tavily.api_key
    openai = settings.api.openai.api_key
    missing = []
    if not tavily:
        missing.append("TAVILY_API_KEY")
    if not openai:
        missing.append("OPENAI_API_KEY")

    if missing:
        raise InvalidAPIKeyError(f"Missing keys: {', '.join(missing)}")
    click.echo("API keys are configured.")


@cli.command(name="scrape-tavily")
@click.option("--topic", required=True, help="Topic to search")
@click.option("--limit", type=int, default=10)
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=Path("config.yaml"))
def scrape_tavily(topic: str, limit: int, config_path: Path) -> None:
    """Scrape content using Tavily."""
    load_dotenv()
    setup_logger()
    _ = get_settings(config_path)

    async def _run() -> None:
        from ..scrapers.tavily_scraper import TavilyScraper

        scraper = TavilyScraper()
        try:
            docs = await scraper.scrape(topic, limit)
            # Ensure output directory exists
            out_dir = Path("data/raw")
            out_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            out_path = out_dir / f"tavily_{ts}.jsonl"
            # Stream JSONL
            with out_path.open("w", encoding="utf-8") as f:
                for d in docs:
                    record = {
                        "title": d.title,
                        "url": d.url,
                        "score": d.source_score,
                        "content": d.content,
                        "timestamp": datetime.now().isoformat(),
                    }
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
            click.echo(f"Saved {len(docs)} documents to ./data/raw/{out_path.name}")
        finally:
            await scraper.close()

    asyncio.run(_run())


if __name__ == "__main__":
    cli()
