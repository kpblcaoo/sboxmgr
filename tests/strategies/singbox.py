"""
Sing-box fuzzing strategies for Hypothesis.

This module contains strategies for generating valid sing-box configurations
for property-based testing against both Pydantic models and sing-box binary.
"""

from hypothesis import strategies as st
from hypothesis.strategies import (
    booleans,
    builds,
    integers,
    lists,
    one_of,
    sampled_from,
    text,
)

# ============================================================================
# BASIC STRATEGIES
# ============================================================================


def valid_ip_strategy():
    """Generate valid IP addresses for sing-box."""
    return sampled_from(
        ["127.0.0.1", "0.0.0.0", "::1", "::", "192.168.1.1", "10.0.0.1", "172.16.0.1"]
    )


def valid_uuid_strategy():
    """Generate valid UUIDs for sing-box protocols."""
    return sampled_from(
        [
            "00000000-0000-0000-0000-000000000000",
            "11111111-1111-1111-1111-111111111111",
            "22222222-2222-2222-2222-222222222222",
            "33333333-3333-3333-3333-333333333333",
            "44444444-4444-4444-4444-444444444444",
        ]
    )


def unique_tag_strategy(prefix=""):
    """Generate unique tags with prefix for sing-box components."""
    return text(min_size=3, max_size=8, alphabet="abcdefghijklmnopqrstuvwxyz").map(
        lambda x: f"{prefix}{x}"
    )


def tls_config_strategy():
    """Generate TLS configuration strategy."""
    return builds(
        dict,
        enabled=booleans(),
        server_name=text(
            min_size=4, max_size=32, alphabet="abcdefghijklmnopqrstuvwxyz"
        ),
        insecure=booleans(),
        alpn=lists(
            text(min_size=2, max_size=10, alphabet="abcdefghijklmnopqrstuvwxyz"),
            min_size=1,
            max_size=3,
        ),
    )


# ============================================================================
# OUTBOUND STRATEGIES
# ============================================================================


def vless_outbound_strategy(tag):
    """Generate VLESS outbound with specific tag."""
    return builds(
        dict,
        type=st.just("vless"),
        tag=st.just(tag),
        server=valid_ip_strategy(),
        server_port=integers(min_value=1, max_value=65535),
        uuid=valid_uuid_strategy(),
        tls=tls_config_strategy(),
    )


def vmess_outbound_strategy(tag):
    """Generate VMess outbound with specific tag."""
    return builds(
        dict,
        type=st.just("vmess"),
        tag=st.just(tag),
        server=valid_ip_strategy(),
        server_port=integers(min_value=1, max_value=65535),
        uuid=valid_uuid_strategy(),
        security=sampled_from(["auto", "aes-128-gcm", "chacha20-poly1305", "none"]),
        alter_id=integers(min_value=0, max_value=100),
    )


def shadowsocks_outbound_strategy(tag):
    """Generate Shadowsocks outbound with specific tag."""
    return builds(
        dict,
        type=st.just("shadowsocks"),
        tag=st.just(tag),
        server=valid_ip_strategy(),
        server_port=integers(min_value=1, max_value=65535),
        method=sampled_from(["aes-256-gcm", "aes-128-gcm"]),
        password=text(min_size=1, max_size=32, alphabet="abcdefghijklmnopqrstuvwxyz"),
    )


def trojan_outbound_strategy(tag):
    """Generate Trojan outbound with specific tag."""
    return builds(
        dict,
        type=st.just("trojan"),
        tag=st.just(tag),
        server=valid_ip_strategy(),
        server_port=integers(min_value=1, max_value=65535),
        password=text(min_size=1, max_size=32, alphabet="abcdefghijklmnopqrstuvwxyz"),
        tls=tls_config_strategy(),
    )


def direct_outbound_strategy(tag):
    """Generate Direct outbound with specific tag."""
    return builds(dict, type=st.just("direct"), tag=st.just(tag))


def block_outbound_strategy(tag):
    """Generate Block outbound with specific tag."""
    return builds(dict, type=st.just("block"), tag=st.just(tag))


def outbound_strategy(tag):
    """Generate any outbound type with specific tag."""
    return one_of(
        vless_outbound_strategy(tag),
        vmess_outbound_strategy(tag),
        shadowsocks_outbound_strategy(tag),
        trojan_outbound_strategy(tag),
        direct_outbound_strategy(tag),
        block_outbound_strategy(tag),
    )


# ============================================================================
# INBOUND STRATEGIES
# ============================================================================


def http_inbound_strategy(tag):
    """Generate HTTP inbound with specific tag."""
    return builds(
        dict,
        type=st.just("http"),
        tag=st.just(tag),
        listen=valid_ip_strategy(),
        listen_port=integers(min_value=1, max_value=65535),
    )


def socks_inbound_strategy(tag):
    """Generate SOCKS inbound with specific tag."""
    return builds(
        dict,
        type=st.just("socks"),
        tag=st.just(tag),
        listen=valid_ip_strategy(),
        listen_port=integers(min_value=1, max_value=65535),
    )


def mixed_inbound_strategy(tag):
    """Generate Mixed inbound with specific tag."""
    return builds(
        dict,
        type=st.just("mixed"),
        tag=st.just(tag),
        listen=valid_ip_strategy(),
        listen_port=integers(min_value=1, max_value=65535),
    )


def inbound_strategy(tag):
    """Generate any inbound type with specific tag."""
    return one_of(
        http_inbound_strategy(tag),
        socks_inbound_strategy(tag),
        mixed_inbound_strategy(tag),
    )


# ============================================================================
# ROUTING STRATEGIES
# ============================================================================


def route_rule_strategy(available_outbound_tags):
    """Generate route rule with valid outbound reference."""
    return builds(
        dict,
        outbound=sampled_from(available_outbound_tags),
        network=sampled_from(["tcp", "udp", "tcp,udp"]),
    )


# ============================================================================
# MAIN CONFIG STRATEGY
# ============================================================================


def singbox_config_strategy():
    """Generate complete SingBoxConfig strategy with unified tags and edge cases."""
    return st.lists(unique_tag_strategy("out_"), min_size=1, max_size=5).flatmap(
        lambda outbound_tags: builds(
            dict,
            log=builds(
                dict, level=sampled_from(["trace", "debug", "info", "warn", "error"])
            ),
            # Edge case: empty inbounds
            inbounds=st.one_of(
                # Generate unique inbound indices
                st.lists(
                    st.integers(min_value=0, max_value=len(outbound_tags) - 1),
                    min_size=0,
                    max_size=2,
                    unique=True,
                ).map(
                    lambda indices: [
                        inbound_strategy(f"in_{i}").example() for i in indices
                    ]
                ),
                st.just([]),  # Edge case: no inbounds
            ),
            # Generate outbounds with unique tags from the list
            outbounds=st.one_of(
                # Normal case: use unique tags from the generated list
                st.lists(
                    st.integers(min_value=0, max_value=len(outbound_tags) - 1),
                    min_size=1,
                    max_size=len(outbound_tags),
                    unique=True,
                ).map(
                    lambda indices: [
                        outbound_strategy(outbound_tags[i]).example() for i in indices
                    ]
                ),
                # Edge case: no outbounds
                st.just([]),
            ),
            route=builds(
                dict,
                # Edge case: empty rules
                rules=st.one_of(
                    lists(route_rule_strategy(outbound_tags), min_size=0, max_size=3),
                    st.just([]),  # Edge case: no rules
                ),
                final=sampled_from(outbound_tags)
                if outbound_tags
                else st.just("direct"),
            ),
        )
    )


# ============================================================================
# EDGE CASE STRATEGIES
# ============================================================================


def edge_case_configs():
    """Generate edge case configurations for testing."""
    return st.one_of(
        # Minimal config
        st.just(
            {
                "log": {"level": "info"},
                "outbounds": [{"type": "direct", "tag": "direct"}],
                "route": {"final": "direct"},
            }
        ),
        # Empty config (should fail)
        st.just({}),
        # Config with only log
        st.just({"log": {"level": "debug"}}),
        # Config with only inbounds
        st.just(
            {
                "inbounds": [
                    {
                        "type": "http",
                        "tag": "http",
                        "listen": "127.0.0.1",
                        "listen_port": 8080,
                    }
                ]
            }
        ),
    )
