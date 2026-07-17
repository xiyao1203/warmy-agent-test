from __future__ import annotations

from collections.abc import Sequence
from ipaddress import IPv4Address, IPv6Address, ip_address
from typing import Protocol


class IpNetwork(Protocol):
    def __contains__(self, address: object) -> bool: ...


def resolve_client_ip(
    direct_peer: str,
    forwarded_for: str | None,
    trusted_proxies: Sequence[IpNetwork],
) -> str:
    peer = _parse(direct_peer)
    if peer is None:
        return "0.0.0.0"
    if not forwarded_for or not any(peer in network for network in trusted_proxies):
        return str(peer)
    forwarded = _parse(forwarded_for.split(",", 1)[0].strip())
    return str(forwarded or peer)


def _parse(value: str) -> IPv4Address | IPv6Address | None:
    try:
        return ip_address(value)
    except ValueError:
        return None
