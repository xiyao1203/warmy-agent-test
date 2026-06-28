"""用户设置值对象。"""

from enum import StrEnum


class Theme(StrEnum):
    """主题枚举。"""

    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"


class Language(StrEnum):
    """语言枚举。"""

    ZH_CN = "zh-CN"
    EN = "en"
