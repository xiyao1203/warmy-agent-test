from __future__ import annotations

from collections.abc import Awaitable, Callable
from copy import deepcopy


class FailureMinimizer:
    def __init__(self, *, max_attempts: int) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        self._max_attempts = max_attempts

    async def minimize(
        self,
        snapshot: dict[str, object],
        reproduce: Callable[[dict[str, object]], Awaitable[str | None]],
    ) -> dict[str, object]:
        result = deepcopy(snapshot)
        expected = await reproduce(result)
        if expected is None:
            raise ValueError("original failure does not reproduce")
        attempts = 1
        for parent_key in tuple(result):
            parent = result.get(parent_key)
            if not isinstance(parent, dict):
                continue
            for key in tuple(parent):
                if attempts >= self._max_attempts:
                    return result
                candidate = deepcopy(result)
                nested = candidate.get(parent_key)
                if not isinstance(nested, dict):
                    continue
                nested.pop(key, None)
                attempts += 1
                if await reproduce(candidate) == expected:
                    result = candidate
        return result
