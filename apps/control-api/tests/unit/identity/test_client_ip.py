from ipaddress import ip_network

from agenttest.modules.identity.api.client_ip import resolve_client_ip


def test_forwarded_header_is_ignored_for_untrusted_peer() -> None:
    assert resolve_client_ip("198.51.100.4", "203.0.113.9", ()) == "198.51.100.4"


def test_first_forwarded_address_is_used_for_trusted_peer() -> None:
    trusted = (ip_network("10.0.0.0/8"),)

    assert resolve_client_ip("10.1.2.3", "203.0.113.9, 10.1.2.3", trusted) == "203.0.113.9"


def test_invalid_forwarded_address_falls_back_to_direct_peer() -> None:
    trusted = (ip_network("10.0.0.0/8"),)

    assert resolve_client_ip("10.1.2.3", "not-an-ip, 10.1.2.3", trusted) == "10.1.2.3"


def test_ipv6_addresses_are_normalized() -> None:
    trusted = (ip_network("2001:db8:1::/48"),)

    assert resolve_client_ip("2001:db8:1::1", "2001:0db8:0002::0001", trusted) == "2001:db8:2::1"
