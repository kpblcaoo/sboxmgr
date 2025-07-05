"""DNS models for sing-box configuration."""

from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional, Union, Dict, Any
from .enums import DomainStrategy

class DnsServer(BaseModel):
    """DNS server configuration."""

    tag: Optional[str] = Field(default=None, description="Unique tag for the DNS server.")
    address: str = Field(..., description="DNS server address, e.g., 8.8.8.8 or https://dns.google/dns-query.")
    address_resolver: Optional[str] = Field(default=None, description="Tag of resolver for this server's address.")
    strategy: Optional[DomainStrategy] = Field(default=None, description="Domain resolution strategy.")
    detours: Optional[List[str]] = Field(default=None, description="List of detour outbound tags.")
    client_ip: Optional[str] = Field(default=None, description="Client IP for DNS queries.")

    model_config = {"extra": "forbid"}

class DnsRule(BaseModel):
    """DNS routing rule."""

    type: str = Field(..., description="Rule type, e.g., 'default', 'logical'.")
    inbound: Optional[List[str]] = Field(default=None, description="List of inbound tags to match.")
    ip_version: Optional[Literal[4, 6]] = Field(default=None, description="IP version to match (4 or 6).")
    network: Optional[str] = Field(default=None, description="Network type to match, e.g., 'tcp', 'udp'.")
    protocol: Optional[List[str]] = Field(default=None, description="Protocols to match, e.g., ['http', 'tls'].")
    domain: Optional[List[str]] = Field(default=None, description="Exact domain names to match.")
    domain_suffix: Optional[List[str]] = Field(default=None, description="Domain suffixes to match.")
    domain_keyword: Optional[List[str]] = Field(default=None, description="Domain keywords to match.")
    domain_regex: Optional[List[str]] = Field(default=None, description="Domain regex patterns to match.")
    geosite: Optional[List[str]] = Field(default=None, description="Geosite categories to match.")
    source_geoip: Optional[List[str]] = Field(default=None, description="Source GeoIP codes to match.")
    source_ip_cidr: Optional[List[str]] = Field(default=None, description="Source IP CIDR ranges to match.")
    source_port: Optional[List[int]] = Field(default=None, description="Source ports to match.")
    source_port_range: Optional[List[str]] = Field(default=None, description="Source port ranges to match, e.g., ['80:90'].")
    port: Optional[List[int]] = Field(default=None, description="Destination ports to match.")
    port_range: Optional[List[str]] = Field(default=None, description="Destination port ranges to match.")
    process_name: Optional[List[str]] = Field(default=None, description="Process names to match.")
    user: Optional[List[str]] = Field(default=None, description="Usernames to match.")
    invert: Optional[bool] = Field(default=None, description="Invert rule matching logic.")
    outbound: Optional[str] = Field(default=None, description="Target outbound tag.")
    server: str = Field(..., description="Target DNS server tag.")

    model_config = {"extra": "forbid"}

class DnsConfig(BaseModel):
    """DNS configuration for sing-box."""

    servers: Optional[List[DnsServer]] = Field(default=None, description="List of DNS servers.")
    rules: Optional[List[DnsRule]] = Field(default=None, description="DNS routing rules.")
    final: Optional[str] = Field(default=None, description="Default DNS server tag.")
    strategy: Optional[DomainStrategy] = Field(default=None, description="Default domain resolution strategy.")
    disable_cache: Optional[bool] = Field(default=None, description="Disable DNS cache.")
    disable_expire: Optional[bool] = Field(default=None, description="Disable DNS cache expiration.")
    independent_cache: Optional[bool] = Field(default=None, description="Use independent DNS cache.")
    reverse_mapping: Optional[bool] = Field(default=None, description="Enable reverse DNS mapping.")
    fakeip: Optional[Dict[str, Any]] = Field(default=None, description="FakeIP settings, e.g., {'enabled': true, 'inet4_range': '198.18.0.0/15'}.")
    hosts: Optional[Dict[str, Union[str, List[str]]]] = Field(default=None, description="Host mappings, e.g., {'example.com': '1.2.3.4'}.")
    client_subnet: Optional[str] = Field(default=None, description="Client subnet for DNS queries, e.g., '1.2.3.0/24'.")

    @field_validator("hosts", mode="before")
    def normalize_hosts(cls, v):
        """Normalize hosts to list of strings."""
        if v:
            return {k: v if isinstance(v, list) else [v] for k, v in v.items()}
        return v

    model_config = {"extra": "forbid"} 