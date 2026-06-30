"""Create stable, git-ignored secrets required by the local development stack."""

from __future__ import annotations

from base64 import urlsafe_b64encode
from os import chmod, urandom
from pathlib import Path


def ensure_local_env(env_file: Path) -> None:
    """Add missing local-only settings without replacing existing values."""

    content = env_file.read_text(encoding="utf-8") if env_file.exists() else ""
    configured = {
        line.split("=", 1)[0].strip()
        for line in content.splitlines()
        if line.strip() and not line.lstrip().startswith("#") and "=" in line
    }
    additions: list[str] = []
    if "AGENTTEST_MODEL_CREDENTIAL_KEY" not in configured:
        key = urlsafe_b64encode(urandom(32)).decode()
        additions.append(f"AGENTTEST_MODEL_CREDENTIAL_KEY={key}")
    if "AGENTTEST_SESSION_COOKIE_SECURE" not in configured:
        additions.append("AGENTTEST_SESSION_COOKIE_SECURE=false")
    if "AGENTTEST_TEMPORAL_ADDRESS" not in configured:
        additions.append("AGENTTEST_TEMPORAL_ADDRESS=localhost:7233")

    if additions:
        separator = "" if not content or content.endswith("\n") else "\n"
        env_file.write_text(
            f"{content}{separator}{'\n'.join(additions)}\n",
            encoding="utf-8",
        )
    chmod(env_file, 0o600)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    ensure_local_env(root / ".env")
    print("Local environment is ready. Secret values were not displayed.")


if __name__ == "__main__":
    main()
