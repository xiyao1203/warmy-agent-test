from pydantic import BaseModel, Field


class ExecutePostprocessStageRequest(BaseModel):
    idempotency_key: str = Field(min_length=1, max_length=300)
    workflow_id: str = Field(min_length=1, max_length=255)
    attempt: int = Field(default=1, ge=1, le=100)


class PostprocessStageResponse(BaseModel):
    status: str
    output: dict[str, object]
    warning_code: str | None = None
