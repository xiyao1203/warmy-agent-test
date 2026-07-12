from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class FakeTargetState:
    scenario: str = "success"
    failures_remaining: int = 0
    delay_seconds: float = 0.05
    attempts: int = 0
    chat_history: list[str] = field(default_factory=list)
    observations: list[dict[str, Any]] = field(default_factory=list)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def configure(
        self, scenario: str, *, failures: int = 0, delay_seconds: float = 0.05
    ) -> None:
        async with self.lock:
            self.scenario = scenario
            self.failures_remaining = max(0, failures)
            self.delay_seconds = max(0.0, delay_seconds)
            self.attempts = 0
            self.chat_history.clear()
            self.observations.clear()

    async def observe(self, request_id: str, input_text: str) -> tuple[int, str, bool]:
        async with self.lock:
            self.attempts += 1
            transient_failure = self.failures_remaining > 0
            if transient_failure:
                self.failures_remaining -= 1
            self.observations.append(
                {
                    "request_id": request_id,
                    "scenario": self.scenario,
                    "attempt": self.attempts,
                    "input": input_text,
                }
            )
            return self.attempts, self.scenario, transient_failure

    async def append_chat(self, message: str) -> tuple[int, list[str]]:
        async with self.lock:
            self.chat_history.append(message)
            return len(self.chat_history), list(self.chat_history)

    async def snapshot(self) -> dict[str, Any]:
        async with self.lock:
            return {
                "scenario": self.scenario,
                "attempts": self.attempts,
                "requests": list(self.observations),
                "chat_history": list(self.chat_history),
            }
