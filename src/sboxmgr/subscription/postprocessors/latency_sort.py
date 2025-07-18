"""Latency-based sorting postprocessor implementation.

This module provides postprocessing functionality for sorting servers
based on latency measurements. It supports various sorting strategies
and can integrate with latency data from profiles or external sources.

Implements Phase 3 architecture with profile integration.
"""

import time
from typing import Any, Optional

from ...configs.models import FullProfile
from ..models import ParsedServer, PipelineContext
from ..registry import register
from .base import ChainablePostProcessor


@register("latency_sort")
class LatencySortPostProcessor(ChainablePostProcessor):
    """Latency-based sorting postprocessor with profile integration.

    Sorts servers based on latency measurements with various strategies.
    Can use cached latency data or perform live measurements.

    Configuration options:
    - sort_order: 'asc' (fastest first) or 'desc' (slowest first)
    - max_latency_ms: Maximum allowed latency in milliseconds
    - timeout_ms: Timeout for latency measurements
    - measurement_method: 'ping', 'tcp', 'http', 'cached'
    - cache_duration_seconds: How long to cache latency measurements
    - fallback_latency: Default latency for servers without measurements
    - remove_unreachable: Whether to remove servers that fail latency tests

    Example:
        processor = LatencySortPostProcessor({
            'sort_order': 'asc',
            'max_latency_ms': 500,
            'timeout_ms': 3000,
            'measurement_method': 'tcp'
        })
        sorted_servers = processor.process(servers, context, profile)

    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """Initialize latency sort processor with configuration.

        Args:
            config: Configuration dictionary with sorting options

        """
        super().__init__(config)
        self.sort_order = self.config.get("sort_order", "asc")
        self.max_latency_ms = self.config.get("max_latency_ms", 1000)
        self.timeout_ms = self.config.get("timeout_ms", 3000)
        self.measurement_method = self.config.get("measurement_method", "cached")
        self.cache_duration_seconds = self.config.get("cache_duration_seconds", 300)
        self.fallback_latency = self.config.get("fallback_latency", 999999)
        self.remove_unreachable = self.config.get("remove_unreachable", False)
        self._latency_cache: dict[
            str, tuple[float, float]
        ] = {}  # server_key -> (latency, timestamp)

    def _do_process(
        self,
        servers: list[ParsedServer],
        context: Optional[PipelineContext] = None,
        profile: Optional[FullProfile] = None,
    ) -> list[ParsedServer]:
        """Sort servers based on latency measurements.

        Args:
            servers: List of servers to sort
            context: Pipeline context
            profile: Full profile configuration

        Returns:
            List of servers sorted by latency

        """
        if not servers:
            return servers

        # Extract latency configuration from profile
        latency_config = self._extract_latency_config(profile)

        # Get latency measurements for all servers
        servers_with_latency = []
        for server in servers:
            latency = self._get_server_latency(server, latency_config, context)

            # Filter by max latency if configured
            if (
                latency_config["max_latency_ms"]
                and latency > latency_config["max_latency_ms"]
            ):
                if not latency_config["remove_unreachable"]:
                    # Keep server but mark as high latency
                    server.meta["high_latency"] = True
                    servers_with_latency.append((server, latency))
                # else: skip server (remove it)
            else:
                servers_with_latency.append((server, latency))

        # Sort by latency
        reverse = latency_config["sort_order"] == "desc"
        servers_with_latency.sort(key=lambda x: x[1], reverse=reverse)

        # Extract sorted servers and add latency metadata
        sorted_servers = []
        for server, latency in servers_with_latency:
            # Add latency information to server metadata
            server.meta["latency_ms"] = latency
            server.meta["latency_measured_at"] = time.time()
            sorted_servers.append(server)

        return sorted_servers

    def _extract_latency_config(self, profile: Optional[FullProfile]) -> dict[str, Any]:
        """Extract latency configuration from profile.

        Args:
            profile: Full profile configuration

        Returns:
            Dictionary with latency configuration

        """
        latency_config = {
            "sort_order": self.sort_order,
            "max_latency_ms": self.max_latency_ms,
            "timeout_ms": self.timeout_ms,
            "measurement_method": self.measurement_method,
            "cache_duration_seconds": self.cache_duration_seconds,
            "fallback_latency": self.fallback_latency,
            "remove_unreachable": self.remove_unreachable,
        }

        if not profile:
            return latency_config

        # Check for latency-specific metadata in profile
        if "latency" in profile.metadata:
            latency_meta = profile.metadata["latency"]
            for key in latency_config:
                if key in latency_meta:
                    latency_config[key] = latency_meta[key]

        # Check agent configuration for latency settings
        if profile.agent and profile.agent.monitor_latency:
            latency_config["measurement_method"] = "tcp"  # Use TCP for agent monitoring

        return latency_config

    def _get_server_latency(
        self,
        server: ParsedServer,
        latency_config: dict[str, Any],
        context: Optional[PipelineContext] = None,
    ) -> float:
        """Get latency measurement for a server.

        Args:
            server: Server to measure latency for
            latency_config: Latency configuration
            context: Pipeline context

        Returns:
            Latency in milliseconds

        """
        server_key = f"{server.address}:{server.port}"

        # Check cache first
        if server_key in self._latency_cache:
            latency, timestamp = self._latency_cache[server_key]
            if time.time() - timestamp < latency_config["cache_duration_seconds"]:
                return latency

        # Check if server already has latency metadata
        if "latency_ms" in server.meta:
            try:
                cached_latency = float(server.meta["latency_ms"])
                # For cached method, always use metadata if available
                if latency_config["measurement_method"] == "cached":
                    self._latency_cache[server_key] = (cached_latency, time.time())
                    return cached_latency
                # For other methods, check if measurement is recent enough
                elif "latency_measured_at" in server.meta:
                    measured_at = float(server.meta["latency_measured_at"])
                    if (
                        time.time() - measured_at
                        < latency_config["cache_duration_seconds"]
                    ):
                        self._latency_cache[server_key] = (cached_latency, measured_at)
                        return cached_latency
            except (ValueError, TypeError):
                pass

        # Perform latency measurement based on method
        method = latency_config["measurement_method"]
        if method == "cached":
            # Use fallback latency for cached-only mode when no metadata available
            latency = latency_config["fallback_latency"]
        elif method == "ping":
            latency = self._measure_ping_latency(server, latency_config)
        elif method == "tcp":
            latency = self._measure_tcp_latency(server, latency_config)
        elif method == "http":
            latency = self._measure_http_latency(server, latency_config)
        else:
            latency = latency_config["fallback_latency"]

        # Cache the measurement
        self._latency_cache[server_key] = (latency, time.time())

        return latency

    def _measure_ping_latency(
        self, server: ParsedServer, config: dict[str, Any]
    ) -> float:
        """Measure latency using ICMP ping.

        Args:
            server: Server to ping
            config: Latency configuration

        Returns:
            Latency in milliseconds

        """
        import platform
        import subprocess

        try:
            # Determine ping command based on OS
            if platform.system().lower() == "windows":
                cmd = [
                    "ping",
                    "-n",
                    "1",
                    "-w",
                    str(config["timeout_ms"]),
                    server.address,
                ]
            else:
                timeout_sec = config["timeout_ms"] / 1000
                cmd = ["ping", "-c", "1", "-W", str(timeout_sec), server.address]

            time.time()
            result = subprocess.run(
                cmd, check=False, capture_output=True, text=True, timeout=timeout_sec
            )

            if result.returncode == 0:
                # Parse ping output for latency (basic implementation)
                output = result.stdout.lower()
                if "time=" in output:
                    # Extract time value (simplified parsing)
                    time_part = output.split("time=")[1].split()[0]
                    return float(time_part.replace("ms", ""))

            return config["fallback_latency"]

        except Exception:
            return config["fallback_latency"]

    def _measure_tcp_latency(
        self, server: ParsedServer, config: dict[str, Any]
    ) -> float:
        """Measure latency using TCP connection.

        Args:
            server: Server to connect to
            config: Latency configuration

        Returns:
            Latency in milliseconds

        """
        import socket

        try:
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(config["timeout_ms"] / 1000)

            result = sock.connect_ex((server.address, server.port))
            end_time = time.time()
            sock.close()

            if result == 0:
                return (end_time - start_time) * 1000
            else:
                return config["fallback_latency"]

        except Exception:
            return config["fallback_latency"]

    def _measure_http_latency(
        self, server: ParsedServer, config: dict[str, Any]
    ) -> float:
        """Measure latency using HTTP request.

        Args:
            server: Server to request
            config: Latency configuration

        Returns:
            Latency in milliseconds

        """
        try:
            import requests

            # Construct URL (basic implementation)
            url = f"http://{server.address}:{server.port}"

            start_time = time.time()
            requests.head(
                url, timeout=config["timeout_ms"] / 1000, allow_redirects=False
            )
            end_time = time.time()

            # Consider any response (even errors) as successful connection
            return (end_time - start_time) * 1000

        except Exception:
            return config["fallback_latency"]

    def pre_process(
        self,
        servers: list[ParsedServer],
        context: Optional[PipelineContext] = None,
        profile: Optional[FullProfile] = None,
    ) -> None:
        """Setup before latency measurements.

        Args:
            servers: List of servers to be processed
            context: Pipeline context
            profile: Full profile configuration

        """
        # Clear old cache entries
        current_time = time.time()
        expired_keys = [
            key
            for key, (_, timestamp) in self._latency_cache.items()
            if current_time - timestamp > self.cache_duration_seconds
        ]
        for key in expired_keys:
            del self._latency_cache[key]

    def can_process(
        self, servers: list[ParsedServer], context: Optional[PipelineContext] = None
    ) -> bool:
        """Check if latency sorting can be applied.

        Args:
            servers: List of servers
            context: Pipeline context

        Returns:
            bool: True if latency sorting is applicable

        """
        return len(servers) > 1  # Only useful if there are multiple servers to sort

    def get_metadata(self) -> dict[str, Any]:
        """Get metadata about this postprocessor.

        Returns:
            Dict containing postprocessor metadata

        """
        metadata = super().get_metadata()
        metadata.update(
            {
                "sort_order": self.sort_order,
                "max_latency_ms": self.max_latency_ms,
                "timeout_ms": self.timeout_ms,
                "measurement_method": self.measurement_method,
                "cache_duration_seconds": self.cache_duration_seconds,
                "fallback_latency": self.fallback_latency,
                "remove_unreachable": self.remove_unreachable,
                "cached_measurements": len(self._latency_cache),
            }
        )
        return metadata
