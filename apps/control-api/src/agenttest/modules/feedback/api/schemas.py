"""反馈 API 模型。"""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FeedbackType(StrEnum):
    """反馈类型枚举。"""

    BUG = "bug"
    FEATURE = "feature"
    UX = "ux"
    OTHER = "other"


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
