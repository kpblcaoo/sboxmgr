"""Inbound configuration builder for CLI parameters.

This module provides the InboundBuilder class for dynamically constructing
ClientProfile objects from CLI parameters, eliminating the need for manual
JSON profile creation while maintaining architectural integrity.
"""

from typing import List, Optional, Union
import typer
from sboxmgr.subscription.models import ClientProfile, InboundProfile


class InboundBuilder:
    """Builder for constructing ClientProfile from CLI parameters.
    
    Provides a fluent interface for building inbound configurations
    with proper validation, security defaults, and error handling.
    
    Example:
        builder = InboundBuilder()
        profile = (builder
            .add_tun(address="198.18.0.1/16", mtu=1500)
            .add_socks(port=1080, listen="127.0.0.1")
            .build())

    """
    
    def __init__(self):
        """Initialize empty inbound builder."""
        self._inbounds: List[InboundProfile] = []
        self._dns_mode: str = "system"
    
    def add_tun(
        self,
        address: Optional[Union[str, List[str]]] = None,
        mtu: Optional[int] = None,
        stack: Optional[str] = None,
        auto_route: bool = True,
        strict_route: bool = True,
        sniff: bool = True,
        **kwargs
    ) -> 'InboundBuilder':
        """Add TUN inbound configuration.
        
        Args:
            address: TUN interface addresses (default: ["198.18.0.1/16"])
            mtu: Maximum transmission unit (default: 1500)
            stack: Network stack implementation (default: "mixed")
            auto_route: Enable automatic routing (default: True)
            strict_route: Enable strict routing (default: True)
            sniff: Enable traffic sniffing (default: True)
            **kwargs: Additional TUN-specific options
            
        Returns:
            Self for method chaining
            
        Raises:
            ValueError: If parameters are invalid

        """
        # Set secure defaults
        if address is None:
            address = ["198.18.0.1/16"]
        elif isinstance(address, str):
            address = [address]
            
        if mtu is None:
            mtu = 1500
        elif not (576 <= mtu <= 9000):
            raise ValueError(f"MTU must be between 576 and 9000, got: {mtu}")
            
        if stack is None:
            stack = "mixed"
        elif stack not in ["system", "gvisor", "mixed"]:
            raise ValueError(f"Invalid stack: {stack}. Must be one of: system, gvisor, mixed")
        
        options = {
            "tag": "tun-in",
            "address": address,
            "mtu": mtu,
            "stack": stack,
            "auto_route": auto_route,
            "strict_route": strict_route,
            "sniff": sniff,
            "sniff_override_destination": False,
            **kwargs
        }
        
        inbound = InboundProfile(type="tun", options=options)
        self._inbounds.append(inbound)
        return self
    
    def add_socks(
        self,
        port: Optional[int] = None,
        listen: Optional[str] = None,
        auth: Optional[str] = None,
        **kwargs
    ) -> 'InboundBuilder':
        """Add SOCKS inbound configuration.
        
        Args:
            port: SOCKS port (default: 1080)
            listen: Bind address (default: "127.0.0.1" for security)
            auth: Authentication in format "user:pass" (optional)
            **kwargs: Additional SOCKS-specific options
            
        Returns:
            Self for method chaining
            
        Raises:
            ValueError: If parameters are invalid

        """
        if port is None:
            port = 1080
        elif not (1024 <= port <= 65535):
            raise ValueError(f"Port must be between 1024 and 65535, got: {port}")
            
        if listen is None:
            listen = "127.0.0.1"
        elif listen == "0.0.0.0":
            typer.echo("⚠️  Warning: SOCKS binding to 0.0.0.0 (all interfaces)", err=True)
        
        options = {
            "tag": "socks-in",
            **kwargs
        }
        
        # Add authentication if provided
        if auth:
            if ":" not in auth:
                raise ValueError("Auth must be in format 'username:password'")
            username, password = auth.split(":", 1)
            options["users"] = [{"username": username, "password": password}]
        
        inbound = InboundProfile(type="socks", listen=listen, port=port, options=options)
        self._inbounds.append(inbound)
        return self
    
    def add_http(
        self,
        port: Optional[int] = None,
        listen: Optional[str] = None,
        auth: Optional[str] = None,
        **kwargs
    ) -> 'InboundBuilder':
        """Add HTTP proxy inbound configuration.
        
        Args:
            port: HTTP proxy port (default: 8080)
            listen: Bind address (default: "127.0.0.1" for security)
            auth: Authentication in format "user:pass" (optional)
            **kwargs: Additional HTTP-specific options
            
        Returns:
            Self for method chaining
            
        Raises:
            ValueError: If parameters are invalid

        """
        if port is None:
            port = 8080
        elif not (1024 <= port <= 65535):
            raise ValueError(f"Port must be between 1024 and 65535, got: {port}")
            
        if listen is None:
            listen = "127.0.0.1"
        elif listen == "0.0.0.0":
            typer.echo("⚠️  Warning: HTTP proxy binding to 0.0.0.0 (all interfaces)", err=True)
        
        options = {
            "tag": "http-in",
            **kwargs
        }
        
        # Add authentication if provided
        if auth:
            if ":" not in auth:
                raise ValueError("Auth must be in format 'username:password'")
            username, password = auth.split(":", 1)
            options["users"] = [{"username": username, "password": password}]
        
        inbound = InboundProfile(type="http", listen=listen, port=port, options=options)
        self._inbounds.append(inbound)
        return self
    
    def add_tproxy(
        self,
        port: Optional[int] = None,
        listen: Optional[str] = None,
        network: Optional[str] = None,
        **kwargs
    ) -> 'InboundBuilder':
        """Add transparent proxy inbound configuration.
        
        Args:
            port: TPROXY port (default: 7895)
            listen: Bind address (default: "0.0.0.0" for TPROXY functionality)
            network: Network type (default: "tcp")
            **kwargs: Additional TPROXY-specific options
            
        Returns:
            Self for method chaining
            
        Raises:
            ValueError: If parameters are invalid

        """
        if port is None:
            port = 7895
        elif not (1024 <= port <= 65535):
            raise ValueError(f"Port must be between 1024 and 65535, got: {port}")
            
        if listen is None:
            listen = "127.0.0.1"  # TPROXY default to localhost for security
            
        if network is None:
            network = "tcp"
        elif network not in ["tcp", "udp", "tcp,udp"]:
            raise ValueError(f"Invalid network: {network}. Must be one of: tcp, udp, tcp,udp")
        
        options = {
            "tag": "tproxy-in",
            "network": network,
            "sniff": True,
            **kwargs
        }
        
        inbound = InboundProfile(type="tproxy", listen=listen, port=port, options=options)
        self._inbounds.append(inbound)
        return self
    
    def set_dns_mode(self, mode: str) -> 'InboundBuilder':
        """Set DNS resolution mode.
        
        Args:
            mode: DNS mode (system, tunnel, off)
            
        Returns:
            Self for method chaining
            
        Raises:
            ValueError: If mode is invalid

        """
        if mode not in ["system", "tunnel", "off"]:
            raise ValueError(f"Invalid DNS mode: {mode}. Must be one of: system, tunnel, off")
        self._dns_mode = mode
        return self
    
    def build(self) -> ClientProfile:
        """Build and return the ClientProfile.
        
        Returns:
            Constructed ClientProfile with all configured inbounds
            
        Raises:
            ValueError: If no inbounds are configured

        """
        if not self._inbounds:
            raise ValueError("At least one inbound must be configured")
        
        return ClientProfile(
            inbounds=self._inbounds,
            dns_mode=self._dns_mode
        )


def build_client_profile_from_cli(
    inbound_types: Optional[str] = None,
    # TUN parameters
    tun_address: Optional[str] = None,
    tun_mtu: Optional[int] = None,
    tun_stack: Optional[str] = None,
    # SOCKS parameters
    socks_port: Optional[int] = None,
    socks_listen: Optional[str] = None,
    socks_auth: Optional[str] = None,
    # HTTP parameters
    http_port: Optional[int] = None,
    http_listen: Optional[str] = None,
    http_auth: Optional[str] = None,
    # TPROXY parameters
    tproxy_port: Optional[int] = None,
    tproxy_listen: Optional[str] = None,
    # General parameters
    dns_mode: Optional[str] = None
) -> Optional[ClientProfile]:
    """Build ClientProfile from CLI parameters.
    
    Convenience function that uses InboundBuilder to construct a ClientProfile
    from individual CLI parameters.
    
    Args:
        inbound_types: Comma-separated list of inbound types (tun,socks,http,tproxy)
        tun_address: TUN interface address
        tun_mtu: TUN MTU value
        tun_stack: TUN network stack
        socks_port: SOCKS proxy port
        socks_listen: SOCKS bind address
        socks_auth: SOCKS authentication (user:pass)
        http_port: HTTP proxy port
        http_listen: HTTP bind address
        http_auth: HTTP authentication (user:pass)
        tproxy_port: TPROXY port
        tproxy_listen: TPROXY bind address
        dns_mode: DNS resolution mode
        
    Returns:
        ClientProfile if inbound_types provided, None otherwise
        
    Raises:
        ValueError: If parameters are invalid or incompatible

    """
    if not inbound_types:
        return None
    
    builder = InboundBuilder()
    
    # Set DNS mode if provided
    if dns_mode:
        builder.set_dns_mode(dns_mode)
    
    # Parse and add each inbound type
    for inbound_type in inbound_types.split(","):
        inbound_type = inbound_type.strip().lower()
        
        if inbound_type == "tun":
            builder.add_tun(
                address=tun_address,
                mtu=tun_mtu,
                stack=tun_stack
            )
        elif inbound_type == "socks":
            builder.add_socks(
                port=socks_port,
                listen=socks_listen,
                auth=socks_auth
            )
        elif inbound_type == "http":
            builder.add_http(
                port=http_port,
                listen=http_listen,
                auth=http_auth
            )
        elif inbound_type == "tproxy":
            builder.add_tproxy(
                port=tproxy_port,
                listen=tproxy_listen
            )
        else:
            raise ValueError(f"Unsupported inbound type: {inbound_type}")
    
    return builder.build()
