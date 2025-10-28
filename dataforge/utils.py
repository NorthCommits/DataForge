from __future__ import annotations

import asyncio
import json
from typing import Any, Awaitable, Callable, Coroutine, Optional

from tenacity import AsyncRetrying, RetryError, retry_if_exception_type, stop_after_attempt, wait_exponential

from .exceptions import APITimeoutError


async def async_retry(
    func: Callable[..., Awaitable[Any]],
    *args: Any,
    attempts: int = 3,
    min_wait: float = 0.2,
    max_wait: float = 2.0,
    retry_on: tuple[type[BaseException], ...] = (Exception,),
    **kwargs: Any,
) -> Any:
    for attempt in AsyncRetrying(
        reraise=True,
        stop=stop_after_attempt(attempts),
        wait=wait_exponential(multiplier=min_wait, max=max_wait),
        retry=retry_if_exception_type(retry_on),
    ):
        with attempt:
            return await func(*args, **kwargs)


async def shielded(coro: Coroutine[Any, Any, Any], timeout: Optional[float] = None) -> Any:
    try:
        return await asyncio.wait_for(asyncio.shield(coro), timeout=timeout)
    except asyncio.TimeoutError as exc:
        raise APITimeoutError("Operation timed out") from exc


def json_dumps_safe(data: Any) -> str:
    try:
        return json.dumps(data, ensure_ascii=False)
    except Exception:
        return "{}"
