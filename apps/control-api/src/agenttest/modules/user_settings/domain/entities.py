"""用户设置实体。"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from agenttest.modules.user_settings.domain.value_objects import Language, Theme


@dataclass(slots=True)
class UserSettings:
    """用户设置实体。"""

    user_id: UUID
    theme: Theme = Theme.SYSTEM
    language: Language = Language.ZH_CN
    email_notifications: bool = True
    push_notifications: bool = False
    test_complete_notifications: bool = True

    def update_theme(self, theme: Theme) -> None:
        self.theme = theme

    def update_language(self, language: Language) -> None:
        self.language = language

    def update_notifications(
        self,
        *,
        email: bool | None = None,
        push: bool | None = None,
        test_complete: bool | None = None,
    ) -> None:
        if email is not None:
            self.email_notifications = email
        if push is not None:
            self.push_notifications = push
        if test_complete is not None:
            self.test_complete_notifications = test_complete
