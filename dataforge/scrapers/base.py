from __future__ import annotations

import abc
from typing import List

from ..types import SourceDocument


class BaseScraper(abc.ABC):
    @abc.abstractmethod
    async def scrape(self, topic: str, limit: int = 10) -> List[SourceDocument]:
        ...
