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

    def export(self, servers: List[ParsedServer], exclusions: List[str] = None, user_routes: List[Dict] = None, context: Dict[str, Any] = None, client_profile: 'Optional[ClientProfile]' = None) -> Dict:
        """Экспортирует конфиг для выбранного клиента с учётом профиля и маршрутов.

        Args:
            servers (List[ParsedServer]): Список серверов.
            exclusions (List[str], optional): Исключения.
            user_routes (List[Dict], optional): Пользовательские маршруты.
            context (Dict, optional): Контекст.
            client_profile (Optional[ClientProfile]): Профиль клиента (если не задан — берётся из self).

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
        # Прокидываем client_profile, если поддерживается экспортером
        if self.export_format == "singbox":
            return exporter(filtered_servers, routes, client_profile=client_profile)
        else:
            return exporter(filtered_servers, routes) 