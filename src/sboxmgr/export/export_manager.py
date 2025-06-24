from typing import List, Dict, Any, Optional
from sboxmgr.subscription.models import ParsedServer, ClientProfile
from .routing.default_router import DefaultRouter
from sboxmgr.subscription.exporters.singbox_exporter import singbox_export

EXPORTER_REGISTRY = {
    "singbox": singbox_export,
    # В будущем: "clash": clash_export, "v2ray": v2ray_export и т.д.
}

class ExportManager:
    def __init__(self, routing_plugin=None, export_format="singbox", client_profile: 'Optional[ClientProfile]' = None):
        """Менеджер экспорта конфигов для разных клиентов.

        Args:
            routing_plugin: Плагин для генерации маршрутов.
            export_format (str): Формат экспорта (singbox, clash, v2ray и др.).
            client_profile (Optional[ClientProfile]): Профиль клиента для генерации секции inbounds.
        """
        self.routing_plugin = routing_plugin or DefaultRouter()
        self.export_format = export_format
        self.client_profile = client_profile

    def export(self, servers: List[ParsedServer], exclusions: List[str] = None, user_routes: List[Dict] = None, context: Dict[str, Any] = None, client_profile: 'Optional[ClientProfile]' = None, skip_version_check: bool = False) -> Dict:
        """Экспортирует конфиг для выбранного клиента с учётом профиля и маршрутов.

        Args:
            servers (List[ParsedServer]): Список серверов.
            exclusions (List[str], optional): Исключения.
            user_routes (List[Dict], optional): Пользовательские маршруты.
            context (Dict, optional): Контекст.
            client_profile (Optional[ClientProfile]): Профиль клиента (если не задан — берётся из self).
            skip_version_check (bool): Пропустить проверку версии.

        Returns:
            Dict: Итоговый конфиг.
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
        """Упрощенный метод для экспорта в sing-box формат.
        
        Args:
            servers (List[ParsedServer]): Список серверов.
            routes (List[Dict], optional): Готовые маршруты.
            client_profile (Optional[ClientProfile]): Профиль клиента.
            singbox_version (Optional[str]): Версия sing-box для совместимости.
            
        Returns:
            Dict: Sing-box конфигурация.
        """
        routes = routes or []
        client_profile = client_profile or self.client_profile
        return singbox_export(servers, routes, client_profile=client_profile, singbox_version=singbox_version) 