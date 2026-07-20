"""项目级大模型配置 API Schema。"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..domain.entities import ModelConfiguration, ProjectModelDefault


class CreateModelConfigRequest(BaseModel):
    """创建模型配置请求。"""

    name: str = Field(min_length=1, max_length=200)
    base_url: str = Field(min_length=1, max_length=2048)
    model_name: str = Field(min_length=1, max_length=200)
    api_key: str = Field(min_length=1, max_length=4096)
    supports_vision: bool = False


class UpdateModelConfigRequest(BaseModel):
    """更新模型配置请求；空 API Key 表示保留。"""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    base_url: str | None = Field(default=None, min_length=1, max_length=2048)
    model_name: str | None = Field(default=None, min_length=1, max_length=200)
    api_key: str | None = Field(default=None, min_length=1, max_length=4096)
    supports_vision: bool | None = None
    enabled: bool | None = None


class SetModelDefaultRequest(BaseModel):
    """设置项目默认模型请求。"""

    model_config_id: str


class ModelConfigResponse(BaseModel):
    """不包含凭证明文或密文的模型配置响应。"""

    id: str
    name: str
    provider_type: str
    base_url: str
    model_name: str
    supports_text: bool
    supports_vision: bool
    enabled: bool
    has_api_key: bool
    api_key_hint: str
    created_at: str
    updated_at: str

    @classmethod
    def from_domain(cls, item: ModelConfiguration) -> ModelConfigResponse:
        """从领域实体创建安全的公开响应。"""

        return cls(
            id=str(item.model_config_id.value),
            name=item.name,
            provider_type=item.provider_type.value,
            base_url=item.base_url,
            model_name=item.model_name,
            supports_text=item.supports_text,
            supports_vision=item.supports_vision,
            enabled=item.enabled,
            has_api_key=bool(item.encrypted_api_key),
            api_key_hint=item.api_key_hint,
            created_at=item.created_at.isoformat(),
            updated_at=item.updated_at.isoformat(),
        )


class ModelConfigListResponse(BaseModel):
    """模型配置列表响应。"""

    items: list[ModelConfigResponse]
    total: int
    page: int | None = None
    page_size: int = 50
    total_pages: int = 0


class ModelDefaultResponse(BaseModel):
    """项目默认模型响应。"""

    purpose: str
    model_config_id: str
    updated_at: str

    @classmethod
    def from_domain(cls, item: ProjectModelDefault) -> ModelDefaultResponse:
        return cls(
            purpose=item.purpose.value,
            model_config_id=str(item.model_config_id.value),
            updated_at=item.updated_at.isoformat(),
        )


class ModelDefaultListResponse(BaseModel):
    """项目默认模型列表响应。"""

    items: list[ModelDefaultResponse]


class TextJudgeRequest(BaseModel):
    """文本裁判测试请求。"""

    input_text: str = Field(max_length=100_000)
    output_text: str = Field(min_length=1, max_length=100_000)
    rubric: str = Field(min_length=1, max_length=10_000)


class VisionJudgeRequest(BaseModel):
    """视觉裁判测试请求。"""

    prompt: str = Field(max_length=20_000)
    image_data_url: str = Field(min_length=1, max_length=15_000_000)
    rubric: str = Field(min_length=1, max_length=10_000)
