from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from ..config import get_settings
from ..exceptions import OpenAIAPIError, CostLimitExceededError
from ..types import GPTAnalysisResult, GPTQualityScores
from .base import BaseAPIClient
from .rate_limiter import TokenBucketRateLimiter
from ..storage.api_cache import APICache
from .cost_tracker_singleton import get_cost_tracker


OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"


class OpenAIClient(BaseAPIClient):
    def __init__(self, api_key: Optional[str] = None, rate_limiter: Optional[TokenBucketRateLimiter] = None) -> None:
        settings = get_settings()
        key = api_key or settings.api.openai.api_key
        super().__init__(key)
        self._client = httpx.AsyncClient(timeout=settings.api.openai.timeout)
        self._rate = rate_limiter or TokenBucketRateLimiter(settings.api.rate_limiting.openai_rpm)
        self._model = settings.api.openai.model
        self._fallback_model = settings.api.openai.fallback_model
        self._temperature = settings.api.openai.temperature
        self._max_tokens = settings.api.openai.max_tokens
        self._cache = APICache()

    async def close(self) -> None:
        await self._client.aclose()

    async def analyze_text(self, text: str) -> GPTAnalysisResult:
        settings = get_settings()
        await self._rate.acquire()
        cache_key = f"model={self._model}|temp={self._temperature}|max={self._max_tokens}|text_hash={hash(text)}"
        cached = await self._cache.get("openai_analyze", cache_key)
        if cached is not None:
            return GPTAnalysisResult(**cached)
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        system_prompt = (
            "You are an assistant that evaluates content quality. Return JSON with keys: "
            "summary, key_points (list), topics (list), scores (object with factual_accuracy, coherence, educational_value, writing_quality, originality)."
        )
        payload: Dict[str, Any] = {
            "model": self._model,
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
        }
        try:
            resp = await self._client.post(OPENAI_CHAT_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        except httpx.RequestError as exc:
            raise OpenAIAPIError(f"HTTP error: {exc}") from exc
        except httpx.HTTPStatusError as exc:
            # Attempt fallback on certain errors
            if exc.response.status_code in (429, 500, 503):
                payload["model"] = self._fallback_model
                resp = await self._client.post(OPENAI_CHAT_URL, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
            else:
                raise OpenAIAPIError(f"Bad status: {exc.response.status_code}") from exc

        choice = data.get("choices", [{}])[0]
        content = choice.get("message", {}).get("content", "{}")
        try:
            parsed: Dict[str, Any] = httpx.Response(200, text=content).json()
        except Exception:
            parsed = {}

        scores = parsed.get("scores", {})
        quality = GPTQualityScores(
            factual_accuracy=scores.get("factual_accuracy"),
            coherence=scores.get("coherence"),
            educational_value=scores.get("educational_value"),
            writing_quality=scores.get("writing_quality"),
            originality=scores.get("originality"),
        )

        usage = data.get("usage", {})
        input_tokens = int(usage.get("prompt_tokens", 0))
        output_tokens = int(usage.get("completion_tokens", 0))
        total_cost = self._estimate_cost_usd(payload["model"], input_tokens, output_tokens)
        # Budget enforcement
        self.check_cost_budget(total_cost)
        tracker = get_cost_tracker()
        if not await tracker.within_budget(total_cost):
            raise CostLimitExceededError("Daily budget exceeded")
        # Persist
        result = GPTAnalysisResult(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_cost_usd=total_cost,
            summary=parsed.get("summary"),
            key_points=parsed.get("key_points"),
            topics=parsed.get("topics"),
            scores=quality,
            raw=data,
        )
        await tracker.add_cost("openai", total_cost)
        await self._cache.set("openai_analyze", cache_key, result.model_dump())
        return result

    def _estimate_cost_usd(self, model: str, in_tokens: int, out_tokens: int) -> float:
        # Baseline cost table (USD per 1K tokens). Adjust as needed; values are placeholders.
        pricing = {
            "gpt-4-turbo-preview": (0.01, 0.03),
            "gpt-3.5-turbo": (0.0005, 0.0015),
        }
        in_rate, out_rate = pricing.get(model, pricing["gpt-3.5-turbo"])
        return (in_tokens / 1000.0) * in_rate + (out_tokens / 1000.0) * out_rate
