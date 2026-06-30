from base64 import urlsafe_b64decode
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from stat import S_IMODE


def load_ensure_local_env():
    script = Path(__file__).resolve().parents[4] / "scripts" / "ensure_local_env.py"
    assert script.exists(), "local environment bootstrap script is missing"
    spec = spec_from_file_location("ensure_local_env", script)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ensure_local_env


def test_ensure_local_env_creates_stable_credential_key(tmp_path) -> None:
    ensure_local_env = load_ensure_local_env()
    env_file = tmp_path / ".env"

    ensure_local_env(env_file)
    first_content = env_file.read_text(encoding="utf-8")
    ensure_local_env(env_file)

    values = dict(
        line.split("=", 1)
        for line in first_content.splitlines()
        if line and not line.startswith("#")
    )
    assert env_file.read_text(encoding="utf-8") == first_content
    assert len(urlsafe_b64decode(values["AGENTTEST_MODEL_CREDENTIAL_KEY"])) == 32
    assert values["AGENTTEST_SESSION_COOKIE_SECURE"] == "false"
    assert values["AGENTTEST_TEMPORAL_ADDRESS"] == "localhost:7233"
    assert S_IMODE(env_file.stat().st_mode) == 0o600


def test_ensure_local_env_preserves_existing_values(tmp_path) -> None:
    ensure_local_env = load_ensure_local_env()
    env_file = tmp_path / ".env"
    env_file.write_text(
        "AGENTTEST_MODEL_CREDENTIAL_KEY=existing-key\n"
        "AGENTTEST_SESSION_COOKIE_SECURE=true\n"
        "CUSTOM=value\n",
        encoding="utf-8",
    )

    ensure_local_env(env_file)

    assert env_file.read_text(encoding="utf-8") == (
        "AGENTTEST_MODEL_CREDENTIAL_KEY=existing-key\n"
        "AGENTTEST_SESSION_COOKIE_SECURE=true\n"
        "CUSTOM=value\n"
        "AGENTTEST_TEMPORAL_ADDRESS=localhost:7233\n"
    )
