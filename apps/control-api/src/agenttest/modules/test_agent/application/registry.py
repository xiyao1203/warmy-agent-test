"""超级 Agent 可委派能力的类型安全注册表。"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from agenttest.modules.test_agent.domain.entities import RiskLevel

CapabilityExecutor = Callable[[object, BaseModel], Awaitable[dict[str, object]]]


@dataclass(frozen=True, slots=True)
class Capability:
    name: str
    version: str
    child_agent: str
    risk: RiskLevel
    input_model: type[BaseModel]
    execute: CapabilityExecutor

    def __post_init__(self) -> None:
        if not self.name or not self.version or not self.child_agent:
            raise ValueError("Capability name, version and child agent are required")


class CapabilityRegistry:
    def __init__(self, capabilities: Iterable[Capability] = ()) -> None:
        self._capabilities: dict[str, Capability] = {}
        for capability in capabilities:
            self.register(capability)

    def register(self, capability: Capability) -> None:
        if capability.name in self._capabilities:
            raise ValueError(f"Capability already registered: {capability.name}")
        self._capabilities[capability.name] = capability

    def resolve(
        self,
        child_agent: str,
        name: str,
        arguments: dict[str, Any],
    ) -> tuple[Capability, BaseModel]:
        try:
            capability = self._capabilities[name]
        except KeyError as error:
            raise KeyError(f"Unknown capability: {name}") from error
        if capability.child_agent != child_agent:
            raise PermissionError(f"Capability {name} is not allowed for child agent {child_agent}")
        return capability, capability.input_model.model_validate(arguments)

    def describe_for(self, child_agent: str) -> list[dict[str, object]]:
        return [
            {
                "name": capability.name,
                "version": capability.version,
                "risk": capability.risk.value,
                "input_schema": capability.input_model.model_json_schema(),
            }
            for capability in self._capabilities.values()
            if capability.child_agent == child_agent
        ]

    def describe_all(self) -> list[dict[str, object]]:
        return [
            {
                "name": capability.name,
                "version": capability.version,
                "child_agent": capability.child_agent,
                "risk": capability.risk.value,
                "input_schema": capability.input_model.model_json_schema(),
            }
            for capability in self._capabilities.values()
        ]
