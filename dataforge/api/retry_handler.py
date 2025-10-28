from __future__ import annotations

from typing import Any, Awaitable, Callable

from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential


async def with_retries(
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
