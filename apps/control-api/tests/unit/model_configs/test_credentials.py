"""项目模型凭证加密测试。"""

from base64 import urlsafe_b64encode
from os import urandom

import pytest
from agenttest.modules.model_configs.infrastructure.credentials import AesGcmCredentialCipher


def cipher() -> AesGcmCredentialCipher:
    return AesGcmCredentialCipher(urlsafe_b64encode(b"k" * 32).decode())


def test_encrypts_and_decrypts_api_key() -> None:
    encrypted = cipher().encrypt("sk-real-secret")
    assert "sk-real-secret" not in encrypted
    assert cipher().decrypt(encrypted) == "sk-real-secret"


def test_uses_random_nonce_for_each_encryption() -> None:
    first = cipher().encrypt("same-key")
    second = cipher().encrypt("same-key")
    assert first != second


def test_rejects_tampered_ciphertext() -> None:
    encrypted = cipher().encrypt("sk-real-secret")
    replacement = "A" if encrypted[-1] != "A" else "B"
    with pytest.raises(ValueError, match="解密"):
        cipher().decrypt(encrypted[:-1] + replacement)


def test_rejects_invalid_master_key_length() -> None:
    with pytest.raises(ValueError, match="32"):
        AesGcmCredentialCipher(urlsafe_b64encode(urandom(16)).decode())
