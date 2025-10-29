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
from .scrape import scrape_tavily_to_jsonl
from .process import process_raw_to_dataset
from .export import export_csv_cmd


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
        out_path = await scrape_tavily_to_jsonl(topic, limit)
        saved_count = sum(1 for _ in out_path.open("r", encoding="utf-8"))
        click.echo(f"\u2713 Saved {saved_count} documents to ./data/raw/{out_path.name}")

    asyncio.run(_run())


@cli.command(name="process")
@click.option("--input", "input_path", type=click.Path(path_type=Path, exists=True), required=True)
@click.option("--output", "output_dir", type=click.Path(path_type=Path), required=True)
@click.option("--export-csv", is_flag=True, help="Export CSV files alongside JSONL outputs")
@click.option("--csv-mode", type=click.Choice(["basic", "detailed", "full"], case_sensitive=False), default="detailed", help="CSV column mode")
def process_cmd(input_path: Path, output_dir: Path, export_csv: bool, csv_mode: str) -> None:
    """Process raw JSONL to cleaned, deduplicated train/val/test dataset."""
    stats = process_raw_to_dataset(input_path, output_dir)
    click.echo(
        f"Processed: total={stats['total']} removed={stats['removed']} final={stats['final']}"
    )

    if export_csv:
        from ..exporters.csv_exporter import ColumnMode, export_splits_to_csv
        export_splits_to_csv(
            input_dir=output_dir,
            output_dir=output_dir,
            mode=ColumnMode(csv_mode.lower()),
            encoding="utf-8",
            delimiter=",",
            include_index=False,
        )
        click.echo("✓ Exported CSV files to output directory")


cli.add_command(export_csv_cmd)


if __name__ == "__main__":
    cli()
