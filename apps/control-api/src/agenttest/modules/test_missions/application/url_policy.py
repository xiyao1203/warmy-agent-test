from __future__ import annotations

import asyncio
import socket
from ipaddress import ip_address
from typing import Protocol
from urllib.parse import urlsplit


class UnsafeTargetUrlError(ValueError):
    pass


class HostAddressResolver(Protocol):
    async def resolve(self, host: str) -> tuple[str, ...]: ...


class SystemHostAddressResolver:
    async def resolve(self, host: str) -> tuple[str, ...]:
        loop = asyncio.get_running_loop()
        try:
            records = await loop.getaddrinfo(host, None, type=socket.SOCK_STREAM)
        except OSError as error:
            raise UnsafeTargetUrlError("Target host cannot be resolved") from error
        return tuple(dict.fromkeys(str(record[4][0]) for record in records))


class TargetUrlPolicy:
    def __init__(self, *, allowed_local_hosts: frozenset[str] = frozenset()) -> None:
        self._allowed_local_hosts = allowed_local_hosts

    def validate(self, value: str, resolved_addresses: tuple[str, ...] = ()) -> str:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise UnsafeTargetUrlError("Target URL must use HTTP or HTTPS")
        if parsed.username is not None or parsed.password is not None:
            raise UnsafeTargetUrlError("Target URL cannot contain credentials")
        host = parsed.hostname.rstrip(".").lower()
        if host in self._allowed_local_hosts:
            return value
        if host == "localhost" or host.endswith(".localhost"):
            raise UnsafeTargetUrlError("Local target URLs are not allowed")
        addresses = resolved_addresses
        try:
            ip_address(host)
        except ValueError:
            pass
        else:
            addresses = (host, *resolved_addresses)
        for raw_address in addresses:
            try:
                address = ip_address(raw_address)
            except ValueError as error:
                raise UnsafeTargetUrlError("Target resolved to an invalid address") from error
            if not address.is_global:
                raise UnsafeTargetUrlError("Private or local target addresses are not allowed")
        return value
