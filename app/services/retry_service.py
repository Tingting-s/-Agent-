from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed


T = TypeVar("T")


def default_retry_decorator(
    attempts: int = 3,
    wait_seconds: int = 1,
    retry_on: type[Exception] = Exception,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    return retry(
        stop=stop_after_attempt(attempts),
        wait=wait_fixed(wait_seconds),
        retry=retry_if_exception_type(retry_on),
        reraise=True,
    )


class RetryService:
    @staticmethod
    def run(func: Callable[..., T], *args, **kwargs) -> T:
        wrapped = default_retry_decorator()(func)
        return wrapped(*args, **kwargs)
