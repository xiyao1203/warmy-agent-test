"""Model Runner 短生命周期凭证解密。"""

from base64 import urlsafe_b64decode

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def decrypt_credential(master_key: str, envelope: str) -> str:
    """解密 Control API 生成的 v1 AES-GCM 凭证信封。"""

    try:
        key = urlsafe_b64decode(master_key.encode())
        if len(key) != 32:
            raise ValueError
        version, encoded = envelope.split(".", 1)
        if version != "v1":
            raise ValueError
        encoded += "=" * (-len(encoded) % 4)
        payload = urlsafe_b64decode(encoded.encode())
        return (
            AESGCM(key)
            .decrypt(
                payload[:12],
                payload[12:],
                b"agenttest:model-credential:v1",
            )
            .decode()
        )
    except (ValueError, InvalidTag, UnicodeDecodeError) as error:
        raise ValueError("项目模型凭证解密失败") from error
