from __future__ import annotations

import os
from base64 import urlsafe_b64decode, urlsafe_b64encode
from uuid import UUID

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class BrowserAuthStateCipher:
    _VERSION = "v1"

    def __init__(self, key: bytes) -> None:
        if len(key) not in {16, 24, 32}:
            raise ValueError("浏览器登录态主密钥长度无效")
        self._cipher = AESGCM(key)

    @staticmethod
    def _aad(project_id: UUID, profile_id: UUID) -> bytes:
        return f"agenttest:browser-auth-state:v1:{project_id}:{profile_id}".encode()

    def encrypt(self, project_id: UUID, profile_id: UUID, plaintext: str) -> str:
        nonce = os.urandom(12)
        ciphertext = self._cipher.encrypt(
            nonce,
            plaintext.encode("utf-8"),
            self._aad(project_id, profile_id),
        )
        payload = urlsafe_b64encode(nonce + ciphertext).decode("ascii").rstrip("=")
        return f"{self._VERSION}.{payload}"

    def decrypt(self, project_id: UUID, profile_id: UUID, envelope: str) -> str:
        try:
            version, encoded = envelope.split(".", 1)
        except ValueError as error:
            raise ValueError("浏览器登录态信封格式无效") from error
        if version != self._VERSION:
            raise ValueError("浏览器登录态信封版本不支持")
        try:
            padded = encoded + "=" * (-len(encoded) % 4)
            payload = urlsafe_b64decode(padded)
            nonce, ciphertext = payload[:12], payload[12:]
            if len(nonce) != 12 or not ciphertext:
                raise ValueError("empty ciphertext")
            plaintext = self._cipher.decrypt(
                nonce,
                ciphertext,
                self._aad(project_id, profile_id),
            )
            return plaintext.decode("utf-8")
        except Exception as error:
            raise ValueError("浏览器登录态解密失败") from error
