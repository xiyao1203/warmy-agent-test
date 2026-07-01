from __future__ import annotations

from base64 import urlsafe_b64decode
from binascii import Error as Base64Error

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

AAD = b"agenttest:model-credential:v1"


def decrypt_credential(envelope: str, encoded_master_key: str) -> str:
    try:
        key = urlsafe_b64decode(encoded_master_key.encode())
        if len(key) != 32:
            raise ValueError
        version, encoded = envelope.split(".", 1)
        if version != "v1":
            raise ValueError
        encoded += "=" * (-len(encoded) % 4)
        payload = urlsafe_b64decode(encoded.encode())
        nonce, encrypted = payload[:12], payload[12:]
        if len(nonce) != 12 or not encrypted:
            raise ValueError
        return AESGCM(key).decrypt(nonce, encrypted, AAD).decode()
    except (ValueError, Base64Error, InvalidTag, UnicodeDecodeError) as error:
        raise ValueError("Credential decryption failed") from error
