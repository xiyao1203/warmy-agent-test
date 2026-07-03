from uuid import uuid4

import pytest
from agenttest.modules.test_agent.domain.entities import (
    ChatGeneration,
    GenerationStatus,
)


def test_generation_cancellation_is_idempotent() -> None:
    generation = ChatGeneration.create(
        project_id=uuid4(), session_id=uuid4(), generation_id=uuid4()
    )
    generation.start("model-streaming-fixed")
    generation.request_cancel()
    generation.cancel("partial")
    generation.cancel("partial")

    assert generation.status is GenerationStatus.CANCELLED
    assert generation.partial_content == "partial"


def test_completed_generation_cannot_be_cancelled() -> None:
    generation = ChatGeneration.create(
        project_id=uuid4(), session_id=uuid4(), generation_id=uuid4()
    )
    generation.start("model-streaming-fixed")
    generation.complete("done")

    with pytest.raises(ValueError, match="terminal"):
        generation.request_cancel()


def test_generation_failure_preserves_partial_content() -> None:
    generation = ChatGeneration.create(
        project_id=uuid4(), session_id=uuid4(), generation_id=uuid4()
    )
    generation.start("model-streaming-fixed")
    generation.update_partial("half")
    generation.fail()

    assert generation.status is GenerationStatus.FAILED
    assert generation.partial_content == "half"
    assert generation.completed_at is not None
