from __future__ import annotations

import os
import socket
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable

TIMEOUT_SECONDS = 60
POLL_INTERVAL_SECONDS = 1


def tcp_check(host: str, port: int) -> Callable[[], bool]:
    def check() -> bool:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            return False

    return check


def http_check(url: str) -> Callable[[], bool]:
    def check() -> bool:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                return 200 <= response.status < 300
        except (OSError, urllib.error.URLError):
            return False

    return check


def wait_for(name: str, check: Callable[[], bool]) -> None:
    deadline = time.monotonic() + TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if check():
            print(f"{name}: ready")
            return
        time.sleep(POLL_INTERVAL_SECONDS)
    raise TimeoutError(f"{name}: unavailable after {TIMEOUT_SECONDS} seconds")


def main() -> int:
    services = (
        (
            "postgresql",
            tcp_check(
                os.getenv("AGENTTEST_POSTGRES_HOST", "127.0.0.1"),
                int(os.getenv("AGENTTEST_POSTGRES_PORT", "5432")),
            ),
        ),
        (
            "redis",
            tcp_check(
                os.getenv("AGENTTEST_REDIS_HOST", "127.0.0.1"),
                int(os.getenv("AGENTTEST_REDIS_PORT", "6379")),
            ),
        ),
        (
            "temporal",
            tcp_check(
                os.getenv("AGENTTEST_TEMPORAL_HOST", "127.0.0.1"),
                int(os.getenv("AGENTTEST_TEMPORAL_PORT", "7233")),
            ),
        ),
        (
            "minio",
            http_check(
                os.getenv(
                    "AGENTTEST_MINIO_HEALTH_URL",
                    "http://127.0.0.1:9000/minio/health/live",
                )
            ),
        ),
    )

    try:
        for name, check in services:
            wait_for(name, check)
    except TimeoutError as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
