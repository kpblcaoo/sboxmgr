"""Geographic policies for sboxmgr.

This module provides policies for geographic restrictions including
country-based and ASN-based filtering.
"""

from typing import Dict, Any, Optional, List, Set
from .base import BasePolicy, PolicyContext, PolicyResult
from .utils import extract_metadata_field, validate_mode


class CountryPolicy(BasePolicy):
    """Policy for country-based restrictions.
    
    Allows or denies servers based on their country code.
    Supports both whitelist and blacklist modes.
    """
    name = "CountryPolicy"
    description = "Restricts servers by country code"
    group = "geo"

    def __init__(self, allowed_countries: Optional[List[str]] = None, 
                 blocked_countries: Optional[List[str]] = None,
                 mode: str = "whitelist"):
        """Initialize country policy.
        
        Args:
            allowed_countries: List of allowed country codes (whitelist mode)
            blocked_countries: List of blocked country codes (blacklist mode)
            mode: 'whitelist' or 'blacklist'
            
        Raises:
            ValueError: If mode is not 'whitelist' or 'blacklist'
        """
        super().__init__()
        validate_mode(mode, ["whitelist", "blacklist"])
        self.allowed_countries = set(allowed_countries or [])
        self.blocked_countries = set(blocked_countries or [])
        self.mode = mode

    def evaluate(self, context: PolicyContext) -> PolicyResult:
        """Evaluate country restrictions.
        
        Args:
            context: Context containing server information
            
        Returns:
            PolicyResult indicating if server is allowed
        """
        server = context.server
        
        if not server:
            return PolicyResult.allow("No server to check")
        
        # Extract country from server
        country = self._extract_country(server)
        if not country:
            return PolicyResult.allow("No country information available")
        
        # Apply policy based on mode
        if self.mode == "whitelist":
            if self.allowed_countries and country not in self.allowed_countries:
                return PolicyResult.deny(
                    f"Country {country} not in allowed list",
                    country=country,
                    allowed_countries=list(self.allowed_countries)
                )
        elif self.mode == "blacklist":
            if country in self.blocked_countries:
                return PolicyResult.deny(
                    f"Country {country} is blocked",
                    country=country,
                    blocked_countries=list(self.blocked_countries)
                )
        
        return PolicyResult.allow(f"Country {country} is allowed")

    def _extract_country(self, server: Any) -> Optional[str]:
        """Extract country code from server object.
        
        Args:
            server: Server object to extract country from
            
        Returns:
            Country code or None if not found
        """
        country = extract_metadata_field(
            server, 
            "country", 
            fallback_fields=["cc", "geo", "location"]
        )
        return str(country).upper() if country else None


class ASNPolicy(BasePolicy):
    """Policy for ASN-based restrictions.
    
    Allows or denies servers based on their Autonomous System Number.
    Useful for blocking specific ISPs or network providers.
    """
    name = "ASNPolicy"
    description = "Restricts servers by ASN"
    group = "geo"

    def __init__(self, allowed_asns: Optional[List[int]] = None,
                 blocked_asns: Optional[List[int]] = None,
                 mode: str = "blacklist"):
        """Initialize ASN policy.
        
        Args:
            allowed_asns: List of allowed ASN numbers (whitelist mode)
            blocked_asns: List of blocked ASN numbers (blacklist mode)
            mode: 'whitelist' or 'blacklist'
            
        Raises:
            ValueError: If mode is not 'whitelist' or 'blacklist'
        """
        super().__init__()
        validate_mode(mode, ["whitelist", "blacklist"])
        self.allowed_asns = set(allowed_asns or [])
        self.blocked_asns = set(blocked_asns or [])
        self.mode = mode

    def evaluate(self, context: PolicyContext) -> PolicyResult:
        """Evaluate ASN restrictions.
        
        Args:
            context: Context containing server information
            
        Returns:
            PolicyResult indicating if server is allowed
        """
        server = context.server
        
        if not server:
            return PolicyResult.allow("No server to check")
        
        # Extract ASN from server
        asn = self._extract_asn(server)
        if not asn:
            return PolicyResult.allow("No ASN information available")
        
        # Apply policy based on mode
        if self.mode == "whitelist":
            if self.allowed_asns and asn not in self.allowed_asns:
                return PolicyResult.deny(
                    f"ASN {asn} not in allowed list",
                    asn=asn,
                    allowed_asns=list(self.allowed_asns)
                )
        elif self.mode == "blacklist":
            if asn in self.blocked_asns:
                return PolicyResult.deny(
                    f"ASN {asn} is blocked",
                    asn=asn,
                    blocked_asns=list(self.blocked_asns)
                )
        
        return PolicyResult.allow(f"ASN {asn} is allowed")

    def _extract_asn(self, server: Any) -> Optional[int]:
        """Extract ASN from server object.
        
        Args:
            server: Server object to extract ASN from
            
        Returns:
            ASN number or None if not found
        """
        asn = extract_metadata_field(
            server, 
            "asn", 
            fallback_fields=["autonomous_system"]
        )
        if asn:
            try:
                return int(asn)
            except (ValueError, TypeError):
                return None
        return None 