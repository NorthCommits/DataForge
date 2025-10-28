from __future__ import annotations

import asyncio
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Optional

from loguru import logger


class APICache:
    """Simple file-based async cache for API responses (JSON serializable)."""

    def __init__(self, base_dir: str | Path = ".dataforge_cache") -> None:
        self._dir = Path(base_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

    def _key_to_path(self, namespace: str, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self._dir / namespace / f"{digest}.json"

    async def get(self, namespace: str, key: str) -> Optional[dict[str, Any]]:
        path = self._key_to_path(namespace, key)
        if not path.exists():
            return None
        async with self._lock:
            try:
                data = path.read_text(encoding="utf-8")
                return json.loads(data)
            except Exception:
                logger.warning("Failed reading cache file: {}", path)
                return None

    async def set(self, namespace: str, key: str, value: dict[str, Any]) -> None:
        path = self._key_to_path(namespace, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        async with self._lock:
            try:
                path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
            except Exception:
                logger.warning("Failed writing cache file: {}", path)

    async def clear(self, namespace: Optional[str] = None) -> None:
        async with self._lock:
            base = self._dir if namespace is None else (self._dir / namespace)
            if not base.exists():
                return
            for p in base.rglob("*.json"):
                try:
                    p.unlink()
                except Exception:
                    logger.warning("Failed deleting cache file: {}", p)
