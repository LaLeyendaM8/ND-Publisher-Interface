import time
from collections.abc import Callable
from typing import TypeVar


T = TypeVar("T")


def call_with_retries(
    fn: Callable[[], T],
    retries: int = 5,
    base_sleep_seconds: float = 2.0,
) -> T:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt == retries:
                break
            time.sleep(base_sleep_seconds * attempt)
    assert last_error is not None
    raise last_error
