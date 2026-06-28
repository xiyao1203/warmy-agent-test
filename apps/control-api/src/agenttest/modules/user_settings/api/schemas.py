"""用户设置 API 模型。"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from agenttest.modules.user_settings.domain.entities import UserSettings
from agenttest.modules.user_settings.domain.value_objects import Language, Theme


class UserSettingsResponse(BaseModel):
    """用户设置响应。"""

    theme: Theme
    language: Language
    email_notifications: bool
    push_notifications: bool
    test_complete_notifications: bool

    @classmethod
    def from_domain(cls, settings: UserSettings) -> UserSettingsResponse:
        return cls(
            theme=settings.theme,
            language=settings.language,
            email_notifications=settings.email_notifications,
            push_notifications=settings.push_notifications,
            test_complete_notifications=settings.test_complete_notifications,
        )


class UpdateSettingsRequest(BaseModel):
    """更新设置请求。"""

    model_config = ConfigDict(extra="forbid")

    theme: Theme | None = None
    language: Language | None = None
    email_notifications: bool | None = None
    push_notifications: bool | None = None
    test_complete_notifications: bool | None = None
