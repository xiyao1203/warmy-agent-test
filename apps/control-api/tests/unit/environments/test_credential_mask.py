"""Unit tests for credential masking utility."""

from __future__ import annotations

from agenttest.modules.environments.api.credential_mask import (
    MASK_VALUE,
    _is_sensitive_key,
    mask_credentials,
)


def test_mask_api_key() -> None:
    data = {"api_key": "sk-1234567890", "name": "test"}
    result = mask_credentials(data)
    assert result["api_key"] == MASK_VALUE
    assert result["name"] == "test"


def test_mask_password() -> None:
    data = {"password": "secret123", "username": "admin"}
    result = mask_credentials(data)
    assert result["password"] == MASK_VALUE
    assert result["username"] == "admin"


def test_mask_nested() -> None:
    data = {
        "name": "env",
        "config": {
            "api_token": "tok-abc",
            "endpoint": "https://api.example.com",
        },
    }
    result = mask_credentials(data)
    assert result["config"]["api_token"] == MASK_VALUE
    assert result["config"]["endpoint"] == "https://api.example.com"


def test_mask_list_of_dicts() -> None:
    data = {
        "accounts": [
            {"username": "admin", "password": "pass1"},
            {"username": "user", "access_key": "key123"},
        ]
    }
    result = mask_credentials(data)
    assert result["accounts"][0]["password"] == MASK_VALUE
    assert result["accounts"][0]["username"] == "admin"
    assert result["accounts"][1]["access_key"] == MASK_VALUE


def test_mask_empty_string_not_masked() -> None:
    data = {"api_key": ""}
    result = mask_credentials(data)
    assert result["api_key"] == ""


def test_mask_non_string_values() -> None:
    data = {"api_key": 12345, "secret": True}
    result = mask_credentials(data)
    # Non-string values under sensitive keys get masked to MASK_VALUE
    assert result["api_key"] == MASK_VALUE
    assert result["secret"] == MASK_VALUE


def test_is_sensitive_key() -> None:
    assert _is_sensitive_key("api_key") is True
    assert _is_sensitive_key("API_KEY") is True
    assert _is_sensitive_key("api-key") is True
    assert _is_sensitive_key("apiKey") is True
    assert _is_sensitive_key("password") is True
    assert _is_sensitive_key("SECRET_TOKEN") is True
    assert _is_sensitive_key("access_key") is True
    assert _is_sensitive_key("private_key") is True
    assert _is_sensitive_key("credentials") is True
    assert _is_sensitive_key("auth_token") is True
    assert _is_sensitive_key("name") is False
    assert _is_sensitive_key("endpoint") is False
    assert _is_sensitive_key("description") is False
    assert _is_sensitive_key("timeout") is False


def test_mask_preserves_original() -> None:
    """确保不修改原始字典。"""
    data = {"api_key": "secret", "name": "test"}
    mask_credentials(data)
    assert data["api_key"] == "secret"


def test_mask_deep_nested_auth() -> None:
    data = {
        "services": {
            "llm": {
                "api_key": "sk-xxx",
                "model": "gpt-4",
            },
            "storage": {
                "secret_key": "aws-secret",
                "bucket": "my-bucket",
            },
        }
    }
    result = mask_credentials(data)
    assert result["services"]["llm"]["api_key"] == MASK_VALUE
    assert result["services"]["llm"]["model"] == "gpt-4"
    assert result["services"]["storage"]["secret_key"] == MASK_VALUE
    assert result["services"]["storage"]["bucket"] == "my-bucket"
