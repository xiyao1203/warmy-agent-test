"""反馈 Application 对外部能力的端口。"""

from __future__ import annotations

from typing import Protocol

from agenttest.modules.feedback.domain.entities import Feedback


class FeedbackRepository(Protocol):
    """反馈持久化端口。"""

    async def save(self, feedback: Feedback) -> None:
        """保存一条反馈。"""
        ...
