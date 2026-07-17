"""反馈 API 模型。"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from agenttest.modules.feedback.domain.value_objects import FeedbackType


class CreateFeedbackRequest(BaseModel):
    """创建反馈请求。"""

    model_config = ConfigDict(extra="forbid")

    type: FeedbackType
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=10, max_length=5000)
    contact: str | None = Field(default=None, max_length=320)


class FeedbackResponse(BaseModel):
    """反馈响应。"""

    id: UUID
    type: FeedbackType
    title: str
    description: str
    contact: str | None
    user_id: UUID | None
    created_at: str
