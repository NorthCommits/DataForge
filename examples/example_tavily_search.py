from __future__ import annotations

import asyncio
from pathlib import Path

from dotenv import load_dotenv

from dataforge.api.tavily_client import TavilyClient
from dataforge.api.openai_client import OpenAIClient
from dataforge.config import get_settings
from dataforge.logger import setup_logger


async def main() -> None:
    load_dotenv()
    setup_logger()
    settings = get_settings(Path("config.yaml"))

    tclient = TavilyClient()
    oclient = OpenAIClient()

    try:
        res = await tclient.search("AI research breakthroughs 2024", max_results=3)
        print(f"Found {res.total_results} documents")
        combined_text = "\n\n".join([doc.title or doc.url for doc in res.documents])
        analysis = await oclient.analyze_text(combined_text)
        print(f"Summary: {analysis.summary}")
        print(f"Topics: {analysis.topics}")
        print(f"Cost (USD): {analysis.total_cost_usd:.4f}")
    finally:
        await tclient.close()
        await oclient.close()


if __name__ == "__main__":
    asyncio.run(main())
