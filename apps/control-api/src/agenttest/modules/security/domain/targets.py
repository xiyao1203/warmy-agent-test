from __future__ import annotations

from ipaddress import ip_address
from urllib.parse import urlparse


def validate_agent_endpoint(
    endpoint: str,
    *,
    allow_private_network: bool = False,
) -> None:
    parsed = urlparse(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Agent endpoint must be an HTTP(S) URL")
    if parsed.hostname.lower() == "localhost" and not allow_private_network:
        raise ValueError("Agent endpoint cannot target a private network")
    try:
        address = ip_address(parsed.hostname)
    except ValueError:
        return
    if (
        address.is_private or address.is_loopback or address.is_link_local or address.is_reserved
    ) and not allow_private_network:
        raise ValueError("Agent endpoint cannot target a private network")
