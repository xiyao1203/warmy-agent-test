"""项目模型配置领域规则测试。"""

from uuid import uuid4

import pytest
from agenttest.modules.identity.public import UserId
from agenttest.modules.model_configs.domain.entities import ModelConfiguration
from agenttest.modules.model_configs.domain.value_objects import ModelPurpose, ProviderType
from agenttest.modules.projects.public import ProjectId


def create_config(**overrides: object) -> ModelConfiguration:
    values: dict[str, object] = {
        "project_id": ProjectId(uuid4()),
        "name": "主模型",
        "provider_type": ProviderType.OPENAI_COMPATIBLE,
        "base_url": "https://api.example.com/v1/",
        "model_name": "example-chat",
        "encrypted_api_key": "v1.secret",
        "api_key_hint": "...cdef",
        "supports_text": True,
        "supports_vision": False,
        "created_by": UserId(uuid4()),
    }
    values.update(overrides)
    return ModelConfiguration.create(**values)  # type: ignore[arg-type]


def test_normalizes_openai_compatible_base_url() -> None:
    config = create_config()
    assert config.base_url == "https://api.example.com/v1"


@pytest.mark.parametrize("url", ["ftp://example.com/v1", "https://user:pass@example.com/v1"])
def test_rejects_unsafe_base_url(url: str) -> None:
    with pytest.raises(ValueError):
        create_config(base_url=url)


def test_requires_text_capability() -> None:
    with pytest.raises(ValueError, match="文本"):
        create_config(supports_text=False)


def test_vision_default_requires_vision_capability() -> None:
    config = create_config()
    with pytest.raises(ValueError, match="视觉"):
        config.ensure_usable_for(ModelPurpose.VISION_JUDGE)


def test_disabled_config_cannot_be_used_as_default() -> None:
    config = create_config()
    config.disable()
    with pytest.raises(ValueError, match="停用"):
        config.ensure_usable_for(ModelPurpose.TEST_AGENT_CHAT)


def test_api_key_hint_never_contains_full_key() -> None:
    assert ModelConfiguration.api_key_hint_for("sk-example-secret") == "...cret"
