from __future__ import annotations

import abc
from typing import Any, Optional

from loguru import logger

from ..exceptions import CostLimitExceededError, InvalidAPIKeyError
from ..config import get_settings


class BaseAPIClient(abc.ABC):
    """Abstract base class for API clients with cost tracking hooks."""

    def __init__(self, api_key: Optional[str]) -> None:
        if not api_key:
            raise InvalidAPIKeyError("Missing API key")
        self._api_key = api_key

    @abc.abstractmethod
    async def close(self) -> None:
        ...

    # Cost hooks
    def before_request(self, context: Optional[dict[str, Any]] = None) -> None:
        logger.debug("Before request: {}", context)

    def after_request(self, context: Optional[dict[str, Any]] = None) -> None:
        logger.debug("After request: {}", context)

    def check_cost_budget(self, estimated_cost_usd: float) -> None:
        settings = get_settings()
        per_req_max = settings.api.cost_limits.per_request_max
        if estimated_cost_usd > per_req_max:
            raise CostLimitExceededError("Estimated cost exceeds per-request limit")
