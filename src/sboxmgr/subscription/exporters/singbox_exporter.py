"""
DEPRECATED: Sing-box configuration exporter implementation.

This module is deprecated and will be replaced by the new sing-box exporter
that uses the modular Pydantic models from src.sboxmgr.models.singbox.

The new exporter provides better validation, type safety, and maintainability.
Use the new exporter for all new development.

This module provides comprehensive sing-box configuration export functionality
including server conversion, routing rule generation, and version compatibility
handling. It supports both modern and legacy sing-box syntax for maximum
compatibility across different sing-box versions.
"""
import json
import logging
import warnings
from typing import List, Optional, Dict, Any, Callable
from ..models import ParsedServer, ClientProfile, PipelineContext
from ..base_exporter import BaseExporter
from ..registry import register

# Import new sing-box models (for future use)
# from sboxmgr.models.singbox import (
#     SingBoxConfig,
#     # Inbounds
#     MixedInbound, SocksInbound, HttpInbound, ShadowsocksInbound,
#     VmessInbound, VlessInbound, TrojanInbound, Hysteria2Inbound,
#     WireGuardInbound, TuicInbound, ShadowTlsInbound, DirectInbound,
#     # Outbounds  
#     ShadowsocksOutbound, VmessOutbound, VlessOutbound, TrojanOutbound,
#     Hysteria2Outbound, WireGuardOutbound, HttpOutbound, SocksOutbound,
#     TuicOutbound, ShadowTlsOutbound, DnsOutbound, DirectOutbound,
#     BlockOutbound, SelectorOutbound, UrlTestOutbound, HysteriaOutbound,
#     AnyTlsOutbound, SshOutbound, TorOutbound,
#     # Common
#     TlsConfig, TransportConfig, MultiplexConfig,
#     # Routing
#     RouteConfig, RouteRule
# )

warnings.warn(
    "src.sboxmgr.subscription.exporters.singbox_exporter is deprecated. "
    "Use the new exporter with modular Pydantic models.",
    DeprecationWarning,
    stacklevel=2
)

logger = logging.getLogger(__name__)

def kebab_to_snake(d):
    """Convert kebab-case keys to snake_case recursively in dictionaries.
    
    Transforms dictionary keys from kebab-case (hyphen-separated) to snake_case
    (underscore-separated) format. This is useful for normalizing configuration
    data between different naming conventions.
    
    Args:
        d: Dictionary, list, or other data structure to process.
        
    Returns:
        Processed data structure with kebab-case keys converted to snake_case.
        Non-dictionary types are returned unchanged.
    """
    if not isinstance(d, dict):
        return d
    return {k.replace('-', '_'): kebab_to_snake(v) for k, v in d.items()}

def generate_inbounds(profile: ClientProfile) -> list:
    """Генерирует секцию inbounds для sing-box config на основе ClientProfile.

    Args:
        profile (ClientProfile): Профиль клиента с описанием inbounds.

    Returns:
        list: Список inbounds для секции 'inbounds' в sing-box config.

    SEC:
        - По умолчанию bind только на localhost (127.0.0.1).
        - Порты по умолчанию безопасные, внешний bind только при явном подтверждении.
        - Валидация через pydantic.
    """
    inbounds = []
    for inbound in profile.inbounds:
        # Создаем базовую структуру inbound
        inb = {
            "type": inbound.type,
            "tag": inbound.options.get("tag", f"{inbound.type}-in") if inbound.options else f"{inbound.type}-in"
        }
        
        # Для tun - особая обработка
        if inbound.type == "tun":
            # Добавляем все поля из options в корень для tun
            if inbound.options:
                for key, value in inbound.options.items():
                    if key != "tag":  # tag уже добавлен
                        inb[key] = value
        else:
            # Для остальных типов добавляем listen и listen_port
            if hasattr(inbound, 'listen') and inbound.listen:
                inb["listen"] = inbound.listen
            if hasattr(inbound, 'port') and inbound.port:
                inb["listen_port"] = inbound.port
            
            # Добавляем остальные поля из options
            if inbound.options:
                for key, value in inbound.options.items():
                    if key not in ["tag", "listen", "port"]:  # Эти поля уже обработаны
                        inb[key] = value
        
        # Убираем None-поля для компактности
        inb = {k: v for k, v in inb.items() if v is not None}
        inbounds.append(inb)
    
    return inbounds


def _get_protocol_dispatcher() -> Dict[str, Callable]:
    """Возвращает словарь диспетчеров для специальных протоколов.
    
    Returns:
        Dict[str, Callable]: Маппинг протокол -> функция экспорта.
    """
    return {
        "wireguard": _export_wireguard,
        "hysteria2": _export_hysteria2,
        "tuic": _export_tuic,
        "shadowtls": _export_shadowtls,
        "anytls": _export_anytls,
        "tor": _export_tor,
        "ssh": _export_ssh,
    }


def _normalize_protocol_type(server_type: str) -> str:
    """Нормализует тип протокола для sing-box.
    
    Args:
        server_type (str): Исходный тип протокола.
        
    Returns:
        str: Нормализованный тип протокола.
    """
    if server_type == "ss":
        return "shadowsocks"
    return server_type


def _is_supported_protocol(protocol_type: str) -> bool:
    """Проверяет поддержку протокола.
    
    Args:
        protocol_type (str): Тип протокола.
        
    Returns:
        bool: True если протокол поддерживается.
    """
    supported_types = {
        "vless", "vmess", "trojan", "ss", "shadowsocks", 
        "wireguard", "hysteria2", "tuic", "shadowtls", 
        "anytls", "tor", "ssh"
    }
    return protocol_type in supported_types



def _create_base_outbound(server: ParsedServer, protocol_type: str) -> Dict[str, Any]:
    """Создаёт базовую структуру outbound.
    
    Args:
        server (ParsedServer): Сервер для экспорта.
        protocol_type (str): Нормализованный тип протокола.
        
    Returns:
        Dict[str, Any]: Базовая структура outbound.
    """
    return {
        "type": protocol_type,
        "server": server.address,
        "server_port": server.port,
    }


def _process_shadowsocks_config(outbound: Dict[str, Any], server: ParsedServer, meta: Dict[str, Any]) -> bool:
    """Обрабатывает конфигурацию Shadowsocks.
    
    Args:
        outbound (Dict[str, Any]): Outbound конфигурация для модификации.
        server (ParsedServer): Исходный сервер.
        meta (Dict[str, Any]): Метаданные сервера.
        
    Returns:
        bool: True если конфигурация валидна, False если нужно пропустить сервер.
    """
    method = meta.get("cipher") or meta.get("method") or server.security
    if not method:
        logger.warning(f"WARNING: shadowsocks outbound without method/cipher, skipping: {server.address}:{server.port}")
        return False
    outbound["method"] = method
    return True


def _process_transport_config(outbound: Dict[str, Any], meta: Dict[str, Any]) -> None:
    """Обрабатывает конфигурацию транспорта (ws, grpc, tcp, udp).
    
    Args:
        outbound (Dict[str, Any]): Outbound конфигурация для модификации.
        meta (Dict[str, Any]): Метаданные сервера для модификации.
    """
    network = meta.pop("network", None)
    if network in ("ws", "grpc"):
        outbound["transport"] = {"type": network}
        for k in list(meta.keys()):
            if k.startswith(network):
                outbound["transport"][k[len(network)+1:]] = meta.pop(k)
    elif network in ("tcp", "udp"):
        outbound["network"] = network


def _process_tls_config(outbound: Dict[str, Any], meta: Dict[str, Any], protocol_type: str) -> None:
    """Обрабатывает конфигурацию TLS/Reality/uTLS.
    
    Args:
        outbound (Dict[str, Any]): Outbound конфигурация для модификации.
        meta (Dict[str, Any]): Метаданные сервера для модификации.
        protocol_type (str): Тип протокола.
    """
    tls: Dict[str, Any] = {}
    
    # Базовая TLS конфигурация
    if meta.get("tls") or meta.get("security") == "tls":
        tls["enabled"] = True
        meta.pop("tls", None)
        meta.pop("security", None)
    
    # Server name
    if meta.get("servername"):
        tls["server_name"] = meta.pop("servername")
    
    # Reality конфигурация
    if meta.get("reality-opts"):
        reality = kebab_to_snake(meta.pop("reality-opts"))
        if "reality" not in tls:
            tls["reality"] = {"enabled": True}
        tls["reality"].update(reality)
    
    if meta.get("pbk"):
        if "reality" not in tls:
            tls["reality"] = {"enabled": True}
        tls["reality"]["public_key"] = meta.pop("pbk")
    
    if meta.get("short_id"):
        if "reality" not in tls:
            tls["reality"] = {"enabled": True}
        tls["reality"]["short_id"] = meta.pop("short_id")
    
    # uTLS конфигурация
    utls_fp = meta.pop("client-fingerprint", None) or meta.pop("fp", None)
    if utls_fp:
        if "utls" not in tls:
            tls["utls"] = {"enabled": True}
        tls["utls"]["fingerprint"] = utls_fp
    
    # ALPN
    if meta.get("alpn"):
        tls["alpn"] = meta.pop("alpn")
    
    # Добавляем TLS конфигурацию только для поддерживающих протоколов
    if tls and protocol_type in {"vless", "vmess", "trojan"}:
        outbound["tls"] = tls


def _process_auth_and_flow_config(outbound: Dict[str, Any], meta: Dict[str, Any]) -> None:
    """Обрабатывает конфигурацию аутентификации и flow.
    
    Args:
        outbound (Dict[str, Any]): Outbound конфигурация для модификации.
        meta (Dict[str, Any]): Метаданные сервера для модификации.
    """
    if meta.get("uuid"):
        outbound["uuid"] = meta.pop("uuid")
    
    if meta.get("flow"):
        outbound["flow"] = meta.pop("flow")


def _process_tag_config(outbound: Dict[str, Any], server: ParsedServer, meta: Dict[str, Any]) -> None:
    """Обрабатывает конфигурацию тега outbound.
    
    Args:
        outbound (Dict[str, Any]): Outbound конфигурация для модификации.
        server (ParsedServer): Исходный сервер.
        meta (Dict[str, Any]): Метаданные сервера для модификации.
    """
    # Приоритет: server.tag > meta.label > meta.name > server.address
    if server.tag:
        outbound["tag"] = server.tag
    elif meta.get("label"):
        outbound["tag"] = meta.pop("label")
    elif meta.get("name"):
        outbound["tag"] = meta.pop("name")
    else:
        outbound["tag"] = server.address


def _process_additional_config(outbound: Dict[str, Any], meta: Dict[str, Any]) -> None:
    """Обрабатывает дополнительные параметры конфигурации.
    
    Args:
        outbound (Dict[str, Any]): Outbound конфигурация для модификации.
        meta (Dict[str, Any]): Метаданные сервера.
    """
    whitelist = {
        "password", "method", "multiplex", "packet_encoding", 
        "udp_over_tcp", "udp_relay_mode", "udp_fragment", "udp_timeout"
    }
    for k, v in meta.items():
        if k in whitelist:
            outbound[k] = v


def _process_standard_server(server: ParsedServer, protocol_type: str) -> Optional[Dict[str, Any]]:
    """Обрабатывает стандартный сервер (не специальный протокол).
    
    Args:
        server (ParsedServer): Сервер для обработки.
        protocol_type (str): Нормализованный тип протокола.
        
    Returns:
        Optional[Dict[str, Any]]: Outbound конфигурация или None если нужно пропустить.
    """
    outbound = _create_base_outbound(server, protocol_type)
    meta = dict(server.meta or {})
    
    # Обрабатываем Shadowsocks конфигурацию
    if protocol_type == "shadowsocks":
        if not _process_shadowsocks_config(outbound, server, meta):
            return None
    
    # Обрабатываем различные аспекты конфигурации
    _process_transport_config(outbound, meta)
    _process_tls_config(outbound, meta, protocol_type)
    _process_auth_and_flow_config(outbound, meta)
    _process_tag_config(outbound, server, meta)
    _process_additional_config(outbound, meta)
    
    return outbound


def _process_single_server(server: ParsedServer) -> Optional[Dict[str, Any]]:
    """Обрабатывает один сервер и возвращает outbound конфигурацию.
    
    Args:
        server (ParsedServer): Сервер для обработки.
        
    Returns:
        Optional[Dict[str, Any]]: Outbound конфигурация или None если нужно пропустить.
    """
    protocol_type = _normalize_protocol_type(server.type)
    
    # Проверяем поддержку протокола
    if not _is_supported_protocol(protocol_type):
        logger.warning(f"Unsupported outbound type: {server.type}, skipping {server.address}:{server.port}")
        return None
    
    # Обрабатываем специальные протоколы
    dispatcher = _get_protocol_dispatcher()
    if protocol_type in dispatcher:
        return dispatcher[protocol_type](server)  # Может вернуть None
    
    # Обрабатываем стандартные протоколы
    return _process_standard_server(server, protocol_type)


def _add_special_outbounds(outbounds: List[Dict[str, Any]]) -> None:
    """Добавляет специальные outbounds (direct, block, dns-out).
    
    DEPRECATED: In sing-box 1.11.0, these special outbounds are deprecated
    and should be replaced with rule actions. This function is kept for
    backward compatibility but will be removed in future versions.
    
    Args:
        outbounds (List[Dict[str, Any]]): Список outbounds для модификации.
    """
    import warnings
    warnings.warn(
        "Special outbounds (direct, block, dns) are deprecated in sing-box 1.11.0. "
        "Use rule actions instead. See: https://sing-box.sagernet.org/migration/#migrate-legacy-special-outbounds-to-rule-actions",
        DeprecationWarning,
        stacklevel=2
    )
    
    tags = {o.get("tag") for o in outbounds}
    if "direct" not in tags:
        outbounds.append({"type": "direct", "tag": "direct"})
    if "block" not in tags:
        outbounds.append({"type": "block", "tag": "block"})
    if "dns-out" not in tags:
        outbounds.append({"type": "dns", "tag": "dns-out"})


def singbox_export_with_middleware(
    servers: List[ParsedServer],
    routes=None,
    client_profile: Optional[ClientProfile] = None,
    context: Optional[PipelineContext] = None
) -> dict:
    """Export parsed servers to sing-box configuration format using middleware.
    
    This function exports configuration using middleware for outbound filtering
    and route configuration, providing better separation of concerns.
    
    Args:
        servers: List of ParsedServer objects to export.
        routes: Routing rules configuration (optional, uses modern defaults if None).
        client_profile: Optional client profile for inbound generation.
        context: Optional pipeline context with middleware metadata.
        
    Returns:
        Dictionary containing complete sing-box configuration with outbounds,
        routing rules, and optional inbounds section.
    """
    outbounds = []
    proxy_tags = []
    
    # Обрабатываем каждый сервер
    for server in servers:
        outbound = _process_single_server(server)
        if outbound:
            outbounds.append(outbound)
            proxy_tags.append(outbound["tag"])
    
    # Добавляем urltest outbound если есть прокси серверы
    if proxy_tags:
        urltest_outbound = {
            "type": "urltest",
            "tag": "auto",
            "outbounds": proxy_tags,
            "url": "https://www.gstatic.com/generate_204",
            "interval": "3m",
            "tolerance": 50,
            "idle_timeout": "30m",
            "interrupt_exist_connections": False
        }
        outbounds.insert(0, urltest_outbound)
    
    # НЕ добавляем специальные outbounds - используем rule actions вместо них
    
    # Используем переданные правила маршрутизации или создаем современные по умолчанию
    if routes:
        routing_rules = routes
    else:
        routing_rules = _create_modern_routing_rules(proxy_tags)
    
    # Определяем final action из context или client_profile
    final_action = "auto"  # по умолчанию
    
    # Приоритет: context > client_profile > default
    if context and 'routing' in context.metadata:
        context_final = context.metadata['routing'].get('final_action')
        if context_final:
            final_action = context_final
    elif client_profile and client_profile.routing:
        final_action = client_profile.routing.get("final", "auto")
    
    # Формируем финальную конфигурацию
    config = {
        "outbounds": outbounds,
        "route": {
            "rules": routing_rules,
            "final": final_action
        }
    }
    
    # Добавляем inbounds если есть client_profile
    if client_profile:
        config["inbounds"] = generate_inbounds(client_profile)
    
    return config


def singbox_export(
    servers: List[ParsedServer],
    routes=None,
    client_profile: Optional[ClientProfile] = None
) -> dict:
    """Export parsed servers to sing-box configuration format (modern approach).
    
    This function exports configuration using the modern sing-box 1.11.0 approach
    with rule actions instead of legacy special outbounds.
    
    Args:
        servers: List of ParsedServer objects to export.
        routes: Routing rules configuration (optional, uses modern defaults if None).
        client_profile: Optional client profile for inbound generation.
        
    Returns:
        Dictionary containing complete sing-box configuration with outbounds,
        routing rules, and optional inbounds section.
    """
    outbounds = []
    proxy_tags = []
    
    # Обрабатываем каждый сервер
    for server in servers:
        outbound = _process_single_server(server)
        if outbound:
            outbounds.append(outbound)
            proxy_tags.append(outbound["tag"])
    
    # Добавляем urltest outbound если есть прокси серверы
    if proxy_tags:
        urltest_outbound = {
            "type": "urltest",
            "tag": "auto",
            "outbounds": proxy_tags,
            "url": "https://www.gstatic.com/generate_204",
            "interval": "3m",
            "tolerance": 50,
            "idle_timeout": "30m",
            "interrupt_exist_connections": False
        }
        outbounds.insert(0, urltest_outbound)
    
    # НЕ добавляем специальные outbounds - используем rule actions вместо них
    
    # Используем переданные правила маршрутизации или создаем современные по умолчанию
    if routes:
        routing_rules = routes
    else:
        routing_rules = _create_modern_routing_rules(proxy_tags)
    
    # Определяем final action
    final_action = "auto" if proxy_tags else "direct"
    
    # Формируем финальную конфигурацию
    config = {
        "outbounds": outbounds,
        "route": {
            "rules": routing_rules,
            "final": final_action
        }
    }
    
    if client_profile is not None:
        config["inbounds"] = generate_inbounds(client_profile)
    
    return config


def _create_modern_routing_rules(proxy_tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Создает современные routing rules с rule actions вместо устаревших special outbounds.
    
    This function creates routing rules that use rule actions instead of
    legacy special outbounds (direct, block, dns) as recommended in sing-box 1.11.0.
    
    Args:
        proxy_tags: List of proxy outbound tags to use in routing rules
        
    Returns:
        List[Dict[str, Any]]: List of routing rules with rule actions
    """
    rules = [
        {
            "protocol": "dns",
            "action": "hijack-dns"
        },
        {
            "ip_is_private": True,
            "action": "direct"
        }
    ]
    
    # Add proxy rule only if we have proxy outbounds
    if proxy_tags:
        rules.append({
            "outbound": "auto"
        })
    else:
        # If no proxies, route everything to direct
        rules.append({
            "action": "direct"
        })
    
    return rules


def _create_enhanced_routing_rules() -> List[Dict[str, Any]]:
    """Создает улучшенные правила маршрутизации как в твоем скрипте."""
    return [
        {
            "protocol": "dns",
            "outbound": "dns-out"
        },
        {
            "ip_is_private": True,
            "outbound": "direct"
        },
        {
            "rule_set": "geoip-ru",
            "outbound": "direct"
        },
        {
            "domain_keyword": [
                "vkontakte",
                "yandex", 
                "tinkoff",
                "gosuslugi",
                "sberbank"
            ],
            "outbound": "direct"
        },
        {
            "domain_suffix": [
                ".ru",
                ".рф",
                "vk.com",
                "sberbank.ru",
                "gosuslugi.ru"
            ],
            "outbound": "direct"
        }
    ]

def _export_wireguard(s: ParsedServer) -> dict:
    """Генерирует outbound-конфиг для WireGuard.

    Args:
        s (ParsedServer): Сервер типа wireguard.

    Returns:
        dict: Outbound-конфиг для sing-box или None (если не хватает обязательных полей).
    """
    required = [s.address, s.port, s.private_key, s.peer_public_key, s.local_address]
    if not all(required):
        logger.warning(f"Incomplete wireguard fields, skipping: {s.address}:{s.port}")
        return None
    out = {
        "type": "wireguard",
        "server": s.address,
        "server_port": s.port,
        "private_key": s.private_key,
        "peer_public_key": s.peer_public_key,
        "local_address": s.local_address,
    }
    if getattr(s, "pre_shared_key", None):
        out["pre_shared_key"] = s.pre_shared_key
    
    # Безопасная проверка meta на None
    meta = getattr(s, 'meta', {}) or {}
    if meta.get("mtu") is not None:
        out["mtu"] = meta["mtu"]
    if meta.get("keepalive") is not None:
        out["keepalive"] = meta["keepalive"]
    
    # Set tag from meta['name'] or server.tag
    if meta.get("name"):
        out["tag"] = meta["name"]
    elif s.tag:
        out["tag"] = s.tag
    else:
        out["tag"] = f"wireguard-{s.address}"
    
    return out

def _export_tuic(s: ParsedServer) -> dict:
    """Генерирует outbound-конфиг для TUIC.
    Args:
        s (ParsedServer): Сервер типа tuic.
    Returns:
        dict: Outbound-конфиг для sing-box или None (если не хватает обязательных полей).
    """
    required = [s.address, s.port, s.uuid, s.password]
    if not all(required):
        logger.warning(f"Incomplete tuic fields, skipping: {s.address}:{s.port}")
        return None
    out = {
        "type": "tuic",
        "server": s.address,
        "server_port": s.port,
        "uuid": s.uuid,
        "password": s.password,
    }
    if s.congestion_control:
        out["congestion_control"] = s.congestion_control
    if not s.alpn:
        out["alpn"] = s.alpn
    
    # Безопасная проверка meta на None
    meta = getattr(s, 'meta', {}) or {}
    if meta.get("udp_relay_mode") is not None:
        out["udp_relay_mode"] = meta["udp_relay_mode"]
    if s.tls:
        out["tls"] = s.tls
    
    # Set tag from meta['name'] or server.tag
    if meta.get("name"):
        out["tag"] = meta["name"]
    elif s.tag:
        out["tag"] = s.tag
    else:
        out["tag"] = f"tuic-{s.address}"
    
    return out

def _export_shadowtls(s: ParsedServer) -> dict:
    """Генерирует outbound-конфиг для ShadowTLS.
    Args:
        s (ParsedServer): Сервер типа shadowtls.
    Returns:
        dict: Outbound-конфиг для sing-box или None (если не хватает обязательных полей).
    """
    required = [s.address, s.port, s.password, s.version]
    if not all(required):
        logger.warning(f"Incomplete shadowtls fields, skipping: {s.address}:{s.port}")
        return None
    out = {
        "type": "shadowtls",
        "server": s.address,
        "server_port": s.port,
        "password": s.password,
        "version": s.version,
    }
    if s.handshake:
        out["handshake"] = s.handshake
    if s.tls:
        out["tls"] = s.tls
    
    # Set tag from meta['name'] or server.tag
    meta = getattr(s, 'meta', {}) or {}
    if meta.get("name"):
        out["tag"] = meta["name"]
    elif s.tag:
        out["tag"] = s.tag
    else:
        out["tag"] = f"shadowtls-{s.address}"
    
    return out

def _export_anytls(s: ParsedServer) -> dict:
    """Генерирует outbound-конфиг для AnyTLS.
    Args:
        s (ParsedServer): Сервер типа anytls.
    Returns:
        dict: Outbound-конфиг для sing-box или None (если не хватает обязательных полей).
    """
    required = [s.address, s.port, s.uuid]
    if not all(required):
        logger.warning(f"Incomplete anytls fields, skipping: {s.address}:{s.port}")
        return None
    out = {
        "type": "anytls",
        "server": s.address,
        "server_port": s.port,
        "uuid": s.uuid,
    }
    if s.tls:
        out["tls"] = s.tls
    
    # Set tag from meta['name'] or server.tag
    meta = getattr(s, 'meta', {}) or {}
    if meta.get("name"):
        out["tag"] = meta["name"]
    elif s.tag:
        out["tag"] = s.tag
    else:
        out["tag"] = f"anytls-{s.address}"
    
    return out

def _export_tor(s: ParsedServer) -> dict:
    """Генерирует outbound-конфиг для Tor.
    Args:
        s (ParsedServer): Сервер типа tor.
    Returns:
        dict: Outbound-конфиг для sing-box или None (если не хватает обязательных полей).
    """
    required = [s.address, s.port]
    if not all(required):
        logger.warning(f"Incomplete tor fields, skipping: {s.address}:{s.port}")
        return None
    out = {
        "type": "tor",
        "server": s.address,
        "server_port": s.port,
    }
    
    # Set tag from meta['name'] or server.tag
    meta = getattr(s, 'meta', {}) or {}
    if meta.get("name"):
        out["tag"] = meta["name"]
    elif s.tag:
        out["tag"] = s.tag
    else:
        out["tag"] = f"tor-{s.address}"
    
    return out

def _export_ssh(s: ParsedServer) -> dict:
    """Генерирует outbound-конфиг для SSH.
    Args:
        s (ParsedServer): Сервер типа ssh.
    Returns:
        dict: Outbound-конфиг для sing-box или None (если не хватает обязательных полей).
    """
    required = [s.address, s.port, s.username]
    if not all(required):
        logger.warning(f"Incomplete ssh fields, skipping: {s.address}:{s.port}")
        return None
    out = {
        "type": "ssh",
        "server": s.address,
        "server_port": s.port,
        "username": s.username,
    }
    if s.password:
        out["password"] = s.password
    if s.private_key:
        out["private_key"] = s.private_key
    if s.tls:
        out["tls"] = s.tls
    
    # Set tag from meta['name'] or server.tag
    meta = getattr(s, 'meta', {}) or {}
    if meta.get("name"):
        out["tag"] = meta["name"]
    elif s.tag:
        out["tag"] = s.tag
    else:
        out["tag"] = f"ssh-{s.address}"
    
    return out

def _export_hysteria2(server):
    """Генерирует outbound-конфиг для Hysteria2.
    Args:
        server (ParsedServer): Сервер типа hysteria2.
    Returns:
        dict: Outbound-конфиг для sing-box или None (если не хватает обязательных полей).
    """
    required = [server.address, server.port, server.password]
    if not all(required):
        logger.warning(f"Incomplete hysteria2 fields, skipping: {server.address}:{server.port}")
        return None
    
    out = {
        "type": "hysteria2",
        "server": server.address,
        "server_port": server.port,
        "password": server.password,
    }
    
    # Set tag from meta['name'] or server.tag
    meta = getattr(server, 'meta', {}) or {}
    if meta.get("name"):
        out["tag"] = meta["name"]
    elif server.tag:
        out["tag"] = server.tag
    else:
        out["tag"] = f"hysteria2-{server.address}"
    
    return out

def singbox_export_legacy(
    servers: List[ParsedServer],
    routes,
    client_profile: Optional[ClientProfile] = None
) -> dict:
    """Export parsed servers to sing-box configuration format (legacy approach).
    
    DEPRECATED: This function uses legacy special outbounds (direct, block, dns)
    which are deprecated in sing-box 1.11.0. Use singbox_export() instead.
    
    Args:
        servers: List of ParsedServer objects to export.
        routes: Routing rules configuration.
        client_profile: Optional client profile for inbound generation.
        
    Returns:
        Dictionary containing complete sing-box configuration with outbounds,
        routing rules, and optional inbounds section.
    """
    import warnings
    warnings.warn(
        "singbox_export_legacy() is deprecated. Use singbox_export() for modern sing-box 1.11.0 compatibility.",
        DeprecationWarning,
        stacklevel=2
    )
    
    outbounds = []
    proxy_tags = []
    
    # Обрабатываем каждый сервер
    for server in servers:
        outbound = _process_single_server(server)
        if outbound:
            outbounds.append(outbound)
            proxy_tags.append(outbound["tag"])
    
    # Добавляем urltest outbound если есть прокси серверы
    if proxy_tags:
        urltest_outbound = {
            "type": "urltest",
            "tag": "auto",
            "outbounds": proxy_tags,
            "url": "https://www.gstatic.com/generate_204",
            "interval": "3m",
            "tolerance": 50,
            "idle_timeout": "30m",
            "interrupt_exist_connections": False
        }
        outbounds.insert(0, urltest_outbound)
    
    # Добавляем специальные outbounds для обратной совместимости
    _add_special_outbounds(outbounds)
    
    # Используем переданные правила маршрутизации или создаем улучшенные по умолчанию
    if routes:
        routing_rules = routes
    else:
        routing_rules = _create_enhanced_routing_rules()
    
    # Формируем финальную конфигурацию
    config = {
        "outbounds": outbounds,
        "route": {
            "rules": routing_rules,
            "rule_set": [
                {
                    "tag": "geoip-ru",
                    "type": "remote",
                    "format": "binary",
                    "url": "https://raw.githubusercontent.com/SagerNet/sing-geoip/rule-set/geoip-ru.srs",
                    "download_detour": "direct"
                }
            ],
            "final": "auto" if proxy_tags else "direct"
        },
        "experimental": {
            "cache_file": {
                "enabled": True
            }
        }
    }
    
    if client_profile is not None:
        config["inbounds"] = generate_inbounds(client_profile)
    
    return config

@register("singbox")
class SingboxExporter(BaseExporter):
    """Sing-box format configuration exporter.
    
    Implements the BaseExporter interface for generating sing-box compatible
    JSON configurations from parsed server data. Handles protocol-specific
    outbound generation and version compatibility.
    """
    
    def export(self, servers: List[ParsedServer]) -> str:
        """Export servers to sing-box JSON configuration string.
        
        Args:
            servers: List of ParsedServer objects to export.
            
        Returns:
            JSON string containing sing-box configuration.
            
        Raises:
            ValueError: If server data is invalid or cannot be exported.
        """
        config = singbox_export(servers, [])
        return json.dumps(config, indent=2, ensure_ascii=False) 