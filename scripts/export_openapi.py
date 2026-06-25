from __future__ import annotations

import json
from pathlib import Path

from agenttest.bootstrap.app import create_app

OUTPUT_PATH = Path("docs/api/openapi.json")


def main() -> None:
    schema = create_app().openapi()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
