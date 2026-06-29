"""项目模型 API Key 的版本化 AES-GCM 加密。"""

from __future__ import annotations

from base64 import urlsafe_b64decode, urlsafe_b64encode
from binascii import Error as Base64Error
from os import urandom

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class AesGcmCredentialCipher:
    """使用 256 位部署主密钥加解密项目模型凭证。"""

    _AAD = b"agenttest:model-credential:v1"

    def __init__(self, encoded_master_key: str) -> None:
        try:
            key = urlsafe_b64decode(encoded_master_key.encode())
        except (ValueError, Base64Error) as error:
            raise ValueError("模型凭证主密钥必须是 URL-safe Base64") from error
        if len(key) != 32:
            raise ValueError("模型凭证主密钥解码后必须为 32 字节")
        self._cipher = AESGCM(key)

    def encrypt(self, plaintext: str) -> str:
        """加密 API Key，并为每次写入生成独立 nonce。"""

        if not plaintext:
            raise ValueError("模型 API Key 不能为空")
        nonce = urandom(12)
        encrypted = self._cipher.encrypt(nonce, plaintext.encode(), self._AAD)
        payload = urlsafe_b64encode(nonce + encrypted).decode().rstrip("=")
        return f"v1.{payload}"

    def decrypt(self, envelope: str) -> str:
        """校验版本和认证标签后解密 API Key。"""

        try:
            version, encoded = envelope.split(".", 1)
            if version != "v1":
                raise ValueError
            encoded += "=" * (-len(encoded) % 4)
            payload = urlsafe_b64decode(encoded.encode())
            nonce, encrypted = payload[:12], payload[12:]
            if len(nonce) != 12 or not encrypted:
                raise ValueError
            return self._cipher.decrypt(nonce, encrypted, self._AAD).decode()
        except (ValueError, Base64Error, InvalidTag, UnicodeDecodeError) as error:
            raise ValueError("模型凭证解密失败") from error
