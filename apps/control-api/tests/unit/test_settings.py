import pytest
from agenttest.bootstrap.settings import Settings
from pydantic import ValidationError


def test_settings_require_database_url() -> None:
    with pytest.raises(ValidationError):
        Settings(database_url="")
