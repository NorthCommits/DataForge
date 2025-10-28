from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from loguru import logger


def setup_logger(log_level: str = "INFO", log_dir: Optional[str | Path] = None) -> None:
    logger.remove()
    logger.add(lambda msg: print(msg, end=""), level=log_level)

    if log_dir:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        logger.add(Path(log_dir) / "dataforge.log", level=log_level, rotation="10 MB", retention="7 days")

    # Reduce noise from libraries
    logger.disable("httpx")
    logger.disable("asyncio")


__all__ = ["logger", "setup_logger"]
