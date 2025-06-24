import json
import logging
from typing import List, Optional, Dict, Any
from ..models import ParsedServer, ClientProfile, InboundProfile
from ..base_exporter import BaseExporter
from ..registry import register
from ...utils.version import should_use_legacy_outbounds

logger = logging.getLogger(__name__)

def kebab_to_snake(d):
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
        # pydantic уже валидирует SEC, но можно добавить дополнительные проверки
        inb = inbound.model_dump(exclude_unset=True)
        # Убираем None-поля для компактности
        inb = {k: v for k, v in inb.items() if v is not None}
        inbounds.append(inb)
    return inbounds

def singbox_export(
    servers: List[ParsedServer],
    routes,
    client_profile: Optional[ClientProfile] = None,
    singbox_version: Optional[str] = None,
    skip_version_check: bool = False
) -> dict:
    """Export parsed servers to sing-box configuration format.
    
    Converts a list of parsed server configurations into a complete sing-box
    configuration with outbounds, routing rules, and optional inbound profiles.
    Supports version compatibility checks and legacy outbound generation.
    
    Args:
        servers: List of ParsedServer objects to export.
        routes: Routing rules configuration.
        client_profile: Optional client profile for inbound generation.
        singbox_version: Optional sing-box version for compatibility checks.
        skip_version_check: Whether to skip version compatibility validation.
        
    Returns:
        Dictionary containing complete sing-box configuration with outbounds,
        routing rules, and optional inbounds section.
        
    Note:
        Automatically adds special outbounds (direct, block, dns-out) based
        on version compatibility. Supports legacy mode for sing-box < 1.11.0.
    """
    supported_types = {"vless", "vmess", "trojan", "ss", "shadowsocks", "wireguard", "hysteria2", "tuic", "shadowtls", "anytls", "tor", "ssh"}
    outbounds = []
    
    # Определяем нужно ли использовать legacy outbounds
    # Если пропускаем проверку версии, используем современный синтаксис
    use_legacy = False if skip_version_check else should_use_legacy_outbounds(singbox_version)
    
    if use_legacy and singbox_version:
        logger.warning(f"Using legacy outbounds for sing-box {singbox_version} compatibility")
    
    for s in servers:
        out_type = s.type
        if out_type == "ss":
            out_type = "shadowsocks"
        if out_type not in supported_types:
            logger.warning(f"Unsupported outbound type: {s.type}, skipping {s.address}:{s.port}")
            continue
        if out_type == "wireguard":
            outbound = _export_wireguard(s)
            if outbound:
                outbounds.append(outbound)
            continue
        if out_type == "hysteria2":
            outbound = _export_hysteria2(s)
            if outbound:
                outbounds.append(outbound)
            continue
        if out_type == "tuic":
            outbound = _export_tuic(s)
            if outbound:
                outbounds.append(outbound)
            continue
        if out_type == "shadowtls":
            outbound = _export_shadowtls(s)
            if outbound:
                outbounds.append(outbound)
            continue
        if out_type == "anytls":
            outbound = _export_anytls(s)
            if outbound:
                outbounds.append(outbound)
            continue
        if out_type == "tor":
            outbound = _export_tor(s)
            if outbound:
                outbounds.append(outbound)
            continue
        if out_type == "ssh":
            outbound = _export_ssh(s)
            if outbound:
                outbounds.append(outbound)
            continue
        out = {
            "type": out_type,
            "server": s.address,
            "server_port": s.port,
        }
        meta = dict(s.meta or {})
        # Shadowsocks: method/cipher
        if out_type == "shadowsocks":
            method = meta.get("cipher") or meta.get("method") or s.security
            if not method:
                logger.warning(f"WARNING: shadowsocks outbound without method/cipher, skipping: {s.address}:{s.port}")
                continue
            out["method"] = method
        # Transport (ws, grpc, etc)
        network = meta.pop("network", None)
        if network in ("ws", "grpc"):
            out["transport"] = {"type": network}
            for k in list(meta.keys()):
                if k.startswith(network):
                    out["transport"][k[len(network)+1:]] = meta.pop(k)
        elif network in ("tcp", "udp"):
            out["network"] = network
        # Группируем tls/reality/utls
        tls = {}
        if meta.get("tls") or meta.get("security") == "tls":
            tls["enabled"] = True
            meta.pop("tls", None)
            meta.pop("security", None)
        if meta.get("servername"):
            tls["server_name"] = meta.pop("servername")
        if meta.get("reality-opts"):
            reality = kebab_to_snake(meta.pop("reality-opts"))
            tls.setdefault("reality", {}).update(reality)
        if meta.get("pbk"):
            tls.setdefault("reality", {})["public_key"] = meta.pop("pbk")
        if meta.get("short_id"):
            tls.setdefault("reality", {})["short_id"] = meta.pop("short_id")
        # utls только внутри tls/utls
        utls_fp = meta.pop("client-fingerprint", None) or meta.pop("fp", None)
        if utls_fp:
            tls.setdefault("utls", {})["fingerprint"] = utls_fp
            tls["utls"]["enabled"] = True
        if meta.get("alpn"):
            tls["alpn"] = meta.pop("alpn")
        if tls and out_type in {"vless", "vmess", "trojan"}:
            out["tls"] = tls
        # uuid, flow, label, tag
        if meta.get("uuid"):
            out["uuid"] = meta.pop("uuid")
        if meta.get("flow"):
            out["flow"] = meta.pop("flow")
        label = meta.pop("label", None)
        if label:
            out["tag"] = label
        elif meta.get("name"):
            out["tag"] = meta.pop("name")
        else:
            out["tag"] = s.address
        whitelist = {"password", "method", "multiplex", "packet_encoding", "udp_over_tcp", "udp_relay_mode", "udp_fragment", "udp_timeout"}
        for k, v in meta.items():
            if k in whitelist:
                out[k] = v
        outbounds.append(out)
    
    tags = {o["tag"] for o in outbounds}
    if "direct" not in tags:
        outbounds.append({"type": "direct", "tag": "direct"})
    
    # Добавляем legacy special outbounds для совместимости с sing-box < 1.11.0
    if use_legacy:
        if "block" not in tags:
            outbounds.append({"type": "block", "tag": "block"})
        if "dns-out" not in tags:
            outbounds.append({"type": "dns", "tag": "dns-out"})
    
    config = {
        "outbounds": outbounds,
        "route": {"rules": routes}
    }
    if client_profile is not None:
        config["inbounds"] = generate_inbounds(client_profile)
    return config

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
    if getattr(s, "mtu", None) is not None:
        out["mtu"] = s.mtu
    if getattr(s, "keepalive", None) is not None:
        out["keepalive"] = s.keepalive
    if s.tag:
        out["tag"] = s.tag
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
    if s.alpn:
        out["alpn"] = s.alpn
    if getattr(s, "udp_relay_mode", None):
        out["udp_relay_mode"] = s.udp_relay_mode
    if s.tls:
        out["tls"] = s.tls
    if s.tag:
        out["tag"] = s.tag
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
    if s.tag:
        out["tag"] = s.tag
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
    if s.tag:
        out["tag"] = s.tag
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
    if s.tag:
        out["tag"] = s.tag
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
    if s.tag:
        out["tag"] = s.tag
    return out

def _export_hysteria2(server):
    required = [server.address, server.port, server.password]
    if not all(required):
        logger.warning(f"Incomplete hysteria2 fields, skipping: {server.address}:{server.port}")
        return None
    return {
        "type": "hysteria2",
        "server": server.address,
        "port": server.port,
        "password": server.password,
        "tag": getattr(server, "tag", server.address),
    }

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
        import json
        return json.dumps(config, indent=2, ensure_ascii=False) 