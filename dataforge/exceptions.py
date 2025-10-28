from __future__ import annotations


class DataForgeError(Exception):
    """Base exception for DataForge."""


class TavilyAPIError(DataForgeError):
    pass


class OpenAIAPIError(DataForgeError):
    pass


class RateLimitExceededError(DataForgeError):
    pass


class CostLimitExceededError(DataForgeError):
    pass


class APITimeoutError(DataForgeError):
    pass


class InvalidAPIKeyError(DataForgeError):
    pass


class InsufficientCreditsError(DataForgeError):
    pass
