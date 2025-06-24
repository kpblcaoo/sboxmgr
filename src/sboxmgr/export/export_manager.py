from typing import List, Dict, Any, Optional
from sboxmgr.subscription.models import ParsedServer, ClientProfile
from .routing.default_router import DefaultRouter
from sboxmgr.subscription.exporters.singbox_exporter import singbox_export

EXPORTER_REGISTRY = {
    "singbox": singbox_export,
    # В будущем: "clash": clash_export, "v2ray": v2ray_export и т.д.
}

class ExportManager:
    """Manages configuration export for various proxy clients.
    
    This class handles the export of parsed server configurations to different
    client formats (sing-box, Clash, v2ray, etc.) with routing rules generation,
    client profile customization, and version compatibility checks.
    
    Attributes:
        routing_plugin: Plugin for generating routing rules.
        export_format: Target export format (singbox, clash, v2ray, etc.).
        client_profile: Client configuration profile for inbound generation.
    """
    
    def __init__(self, routing_plugin=None, export_format="singbox", client_profile: 'Optional[ClientProfile]' = None):
        """Initialize export manager with configuration.

        Args:
            routing_plugin: Optional routing plugin for rule generation. 
                          Defaults to DefaultRouter if not provided.
            export_format: Target export format. Defaults to "singbox".
            client_profile: Optional client profile for inbound configuration.
        """
        self.routing_plugin = routing_plugin or DefaultRouter()
        self.export_format = export_format
        self.client_profile = client_profile

    def export(self, servers: List[ParsedServer], exclusions: List[str] = None, user_routes: List[Dict] = None, context: Dict[str, Any] = None, client_profile: 'Optional[ClientProfile]' = None, skip_version_check: bool = False) -> Dict:
        """Export configuration for the selected client with profile and routing.

        Processes the server list through filtering, routing rule generation,
        and format-specific export with client profile customization and
        version compatibility handling.

        Args:
            servers: List of parsed server configurations to export.
            exclusions: Optional list of server addresses to exclude.
            user_routes: Optional list of custom routing rules.
            context: Optional context dictionary for export customization.
            client_profile: Optional client profile override.
            skip_version_check: Whether to skip version compatibility checks.

        Returns:
            Dictionary containing the final client configuration in the
            specified export format.
            
        Raises:
            ValueError: If the export format is unknown or unsupported.
        """
        exclusions = exclusions or []
        user_routes = user_routes or []
        context = context or {"mode": "default"}
        client_profile = client_profile or self.client_profile
        # 1. Filter servers by exclusions (assume s.address as unique id)
        filtered_servers = [s for s in servers if s.address not in exclusions]
        # 2. Generate routes
        routes = self.routing_plugin.generate_routes(filtered_servers, exclusions, user_routes, context)
        # 3. Делегируем экспорт нужному экспортеру
        exporter = EXPORTER_REGISTRY.get(self.export_format)
        if not exporter:
            raise ValueError(f"Unknown export format: {self.export_format}")
        
        # Прокидываем параметры в экспортер
        if self.export_format == "singbox":
            # Проверяем версию ТОЛЬКО для sing-box формата и только если не пропускаем проверку
            singbox_version = None
            if not skip_version_check:
                from sboxmgr.utils.version import get_singbox_version, check_version_compatibility, get_version_warning_message
                import typer
                
                is_compatible, singbox_version, message = check_version_compatibility()
                if singbox_version:
                    if not is_compatible:
                        typer.echo(f"⚠️  {get_version_warning_message(singbox_version)}", err=True)
                        typer.echo("⚠️  Используется режим совместимости с legacy outbounds", err=True)
                    typer.echo(f"🔧 Detected sing-box version: {singbox_version}")
                else:
                    typer.echo("⚠️  Не удалось определить версию sing-box. Продолжаем с современным синтаксисом.", err=True)
            
            return exporter(filtered_servers, routes, client_profile=client_profile, singbox_version=singbox_version, skip_version_check=skip_version_check)
        else:
            return exporter(filtered_servers, routes)
    
    def export_to_singbox(self, servers: List[ParsedServer], routes: List[Dict] = None, client_profile: 'Optional[ClientProfile]' = None, singbox_version: Optional[str] = None) -> Dict:
        """Simplified method for exporting to sing-box format.
        
        Provides a direct interface for sing-box export without routing
        plugin processing. Useful for cases where routing rules are
        already prepared or not needed.
        
        Args:
            servers: List of server configurations to export.
            routes: Optional pre-prepared routing rules.
            client_profile: Optional client configuration profile.
            singbox_version: Optional sing-box version for compatibility.
            
        Returns:
            Dictionary containing sing-box configuration.
        """
        routes = routes or []
        client_profile = client_profile or self.client_profile
        return singbox_export(servers, routes, client_profile=client_profile, singbox_version=singbox_version) 