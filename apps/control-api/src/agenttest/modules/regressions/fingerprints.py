from __future__ import annotations

import json
from hashlib import sha256


def fingerprint_failure(snapshot: dict[str, object]) -> str:
    semantic = {
        "error_code": snapshot.get("error_code"),
        "tool_chain": snapshot.get("tool_chain", []),
        "input": snapshot.get("input", {}),
    }
    encoded = json.dumps(semantic, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(encoded.encode("utf-8")).hexdigest()
