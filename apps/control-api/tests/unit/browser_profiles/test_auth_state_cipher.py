import json
from uuid import uuid4

import pytest
from agenttest.modules.browser_profiles.infrastructure.auth_state_cipher import (
    BrowserAuthStateCipher,
)


def cipher() -> BrowserAuthStateCipher:
    return BrowserAuthStateCipher(b"k" * 32)


def test_cipher_uses_random_nonce_and_hides_plaintext() -> None:
    project_id = uuid4()
    profile_id = uuid4()
    plaintext = json.dumps({"cookies": [{"name": "session", "value": "secret-token"}]})

    first = cipher().encrypt(project_id, profile_id, plaintext)
    second = cipher().encrypt(project_id, profile_id, plaintext)

    assert first != second
    assert "secret-token" not in first
    assert cipher().decrypt(project_id, profile_id, first) == plaintext


def test_cipher_binds_envelope_to_project_and_profile() -> None:
    project_id = uuid4()
    profile_id = uuid4()
    envelope = cipher().encrypt(project_id, profile_id, '{"cookies":[]}')

    with pytest.raises(ValueError, match="解密"):
        cipher().decrypt(uuid4(), profile_id, envelope)
    with pytest.raises(ValueError, match="解密"):
        cipher().decrypt(project_id, uuid4(), envelope)


def test_cipher_rejects_tampered_or_unknown_envelopes() -> None:
    project_id = uuid4()
    profile_id = uuid4()
    envelope = cipher().encrypt(project_id, profile_id, '{"cookies":[]}')
    replacement = "A" if envelope[-1] != "A" else "B"

    with pytest.raises(ValueError, match="解密"):
        cipher().decrypt(project_id, profile_id, envelope[:-1] + replacement)
    with pytest.raises(ValueError, match="版本"):
        cipher().decrypt(project_id, profile_id, "v2.invalid")
