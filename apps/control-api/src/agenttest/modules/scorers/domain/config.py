from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RuleScorerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    type: Literal["rule"] = "rule"
    operator: Literal["contains", "exact"]
    expected: object


class ReferenceScorerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    type: Literal["reference"] = "reference"
    operator: Literal["contains", "exact"] = "exact"


class ModelScorerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    type: Literal["model"] = "model"
    rubric: str = Field(min_length=1, max_length=4000)
    model_config_id: UUID | None = None


class DeepEvalScorerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    type: Literal["deepeval"] = "deepeval"
    metric: Literal["tool_correctness"] = "tool_correctness"
    expected_tools: list[str] = Field(min_length=1, max_length=50)


ScorerConfig = (
    RuleScorerConfig | ReferenceScorerConfig | ModelScorerConfig | DeepEvalScorerConfig
)


def parse_scorer_config(scorer_type: str, value: dict[str, object]) -> ScorerConfig:
    payload = {**value, "type": scorer_type}
    if scorer_type == "rule":
        return RuleScorerConfig.model_validate(payload)
    if scorer_type == "reference":
        return ReferenceScorerConfig.model_validate(payload)
    if scorer_type == "model":
        return ModelScorerConfig.model_validate(payload)
    if scorer_type == "deepeval":
        return DeepEvalScorerConfig.model_validate(payload)
    raise ValueError(f"Unsupported scorer type: {scorer_type}")
