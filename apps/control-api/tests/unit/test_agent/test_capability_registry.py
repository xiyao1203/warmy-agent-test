from uuid import uuid4

import pytest
from agenttest.modules.test_agent.domain.entities import RiskLevel
from pydantic import BaseModel


class Input(BaseModel):
    project_id: str
    name: str


@pytest.mark.asyncio
async def test_registry_validates_input_and_child_agent_allowlist() -> None:
    from agenttest.modules.test_agent.application.registry import (
        Capability,
        CapabilityRegistry,
    )

    calls = []

    async def execute(context, payload):
        calls.append((context, payload))
        return {"id": str(uuid4())}

    registry = CapabilityRegistry()
    registry.register(
        Capability(
            name="datasets.create",
            version="1",
            child_agent="test_data",
            risk=RiskLevel.DRAFT_WRITE,
            input_model=Input,
            execute=execute,
        )
    )

    capability, payload = registry.resolve(
        "test_data",
        "datasets.create",
        {"project_id": str(uuid4()), "name": "登录回归"},
    )
    result = await capability.execute(object(), payload)

    assert result["id"]
    with pytest.raises(PermissionError, match="not allowed"):
        registry.resolve("security", "datasets.create", payload.model_dump())


def test_registry_rejects_duplicate_and_unknown_capabilities() -> None:
    from agenttest.modules.test_agent.application.registry import (
        Capability,
        CapabilityRegistry,
    )

    async def execute(context, payload):
        return {}

    capability = Capability(
        name="runs.start",
        version="1",
        child_agent="execution",
        risk=RiskLevel.HIGH_IMPACT,
        input_model=Input,
        execute=execute,
    )
    registry = CapabilityRegistry([capability])

    with pytest.raises(ValueError, match="already registered"):
        registry.register(capability)
    with pytest.raises(KeyError, match="Unknown capability"):
        registry.resolve("execution", "runs.cancel", {})
