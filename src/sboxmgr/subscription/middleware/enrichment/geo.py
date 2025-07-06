"""Geographic enrichment functionality for server data."""

import ipaddress
from typing import Any, Dict, Optional

from ...models import ParsedServer, PipelineContext


class GeoEnricher:
    """Provides geographic metadata enrichment for servers.

    Adds geographic information like country, city, coordinates using
    various sources including GeoIP databases and domain TLD analysis.
    """

    def __init__(self, geo_database_path: Optional[str] = None):
        """Initialize geographic enricher.

        Args:
            geo_database_path: Optional path to GeoIP database file
        """
        self.geo_database_path = geo_database_path
        self._cache: Dict[str, Dict[str, Any]] = {}

    def enrich(self, server: ParsedServer, context: PipelineContext) -> ParsedServer:
        """Apply geographic enrichment to a server.

        Args:
            server: Server to enrich
            context: Pipeline context

        Returns:
            Server with geographic enrichment applied
        """
        server_key = server.address

        # Check cache first
        if server_key in self._cache:
            server.meta["geo"] = self._cache[server_key]
            return server

        geo_info = {}

        try:
            # Get geographic information
            geo_info = self._lookup_geographic_info(server.address)

            # Cache the result
            self._cache[server_key] = geo_info

        except Exception as e:
            geo_info["error"] = str(e)

        if geo_info:
            server.meta["geo"] = geo_info

        return server

    def _lookup_geographic_info(self, address: str) -> Dict[str, Any]:
        """Look up geographic information for an address.

        Args:
            address: Server address to look up

        Returns:
            Dictionary with geographic information
        """
        geo_info = {}

        # Skip private/local addresses
        if self._is_private_address(address):
            geo_info["type"] = "private"
            return geo_info

        try:
            # Try using geoip2 if available and database path is provided
            if self.geo_database_path:
                geo_info.update(self._lookup_with_geoip2(address))
            else:
                # Fallback: try to extract country from domain TLD
                geo_info.update(self._lookup_with_tld(address))

        except Exception:
            # If all methods fail, mark as unknown
            geo_info["country"] = "unknown"
            geo_info["source"] = "unknown"

        return geo_info

    def _lookup_with_geoip2(self, address: str) -> Dict[str, Any]:
        """Lookup geographic info using GeoIP2 database.

        Args:
            address: Address to lookup

        Returns:
            Geographic information dictionary
        """
        import geoip2.database
        import geoip2.errors

        geo_info = {}

        with geoip2.database.Reader(self.geo_database_path) as reader:
            response = reader.city(address)
            geo_info.update(
                {
                    "country": response.country.iso_code,
                    "country_name": response.country.name,
                    "city": response.city.name,
                    "latitude": (
                        float(response.location.latitude)
                        if response.location.latitude
                        else None
                    ),
                    "longitude": (
                        float(response.location.longitude)
                        if response.location.longitude
                        else None
                    ),
                    "timezone": response.location.time_zone,
                    "source": "geoip2",
                }
            )

        return geo_info

    def _lookup_with_tld(self, address: str) -> Dict[str, Any]:
        """Lookup geographic info using domain TLD.

        Args:
            address: Address to lookup

        Returns:
            Geographic information dictionary
        """
        geo_info = {}

        # Fallback: try to extract country from domain TLD
        if "." in address and not address.replace(".", "").isdigit():
            tld = address.split(".")[-1].upper()
            if len(tld) == 2:
                geo_info["country"] = tld
                geo_info["source"] = "tld"

        return geo_info

    def _is_private_address(self, address: str) -> bool:
        """Check if address is private/local.

        Args:
            address: Address to check

        Returns:
            True if address is private
        """
        try:
            ip = ipaddress.ip_address(address)
            return ip.is_private or ip.is_loopback or ip.is_link_local
        except ValueError:
            # Not an IP address, assume it's a domain
            return address in ["localhost", "127.0.0.1", "::1"] or address.startswith(
                "192.168."
            )
