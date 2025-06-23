from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, Literal
import uuid
from pydantic import BaseModel, Field, field_validator

@dataclass
class SubscriptionSource:
    url: str
    source_type: str  # url_base64, url_json, file_json, uri_list, ...
    headers: Optional[Dict[str, str]] = None
    label: Optional[str] = None
    user_agent: Optional[str] = None

@dataclass
class ParsedServer:
    """Универсальная модель сервера для подписочного пайплайна.

    Args:
        type (str): Тип протокола (vmess, vless, trojan, ss, wireguard, hysteria2, tuic, shadowtls, anytls, tor, ssh и др.).
        address (str): Адрес сервера (host/IP).
        port (int): Порт сервера.
        security (Optional[str]): Тип шифрования/безопасности (если применимо).
        meta (Dict[str, str]): Дополнительные параметры (legacy/edge-case).
        uuid (Optional[str]): UUID пользователя (vmess, tuic и др.).
        password (Optional[str]): Пароль (trojan, hysteria2, tuic, shadowtls, ssh и др.).
        private_key (Optional[str]): Приватный ключ (wireguard, ssh).
        peer_public_key (Optional[str]): Публичный ключ peer (wireguard).
        pre_shared_key (Optional[str]): Pre-shared key (wireguard).
        local_address (Optional[List[str]]): Локальные адреса (wireguard).
        username (Optional[str]): Имя пользователя (ssh).
        version (Optional[int]): Версия протокола (shadowtls).
        uuid_list (Optional[List[str]]): Список UUID (tuic).
        alpn (Optional[List[str]]): ALPN (hysteria2, tuic).
        obfs (Optional[Dict[str, Any]]): Обфускация (hysteria2).
        tls (Optional[Dict[str, Any]]): TLS-опции (hysteria2, tuic, shadowtls, anytls, ssh).
        handshake (Optional[Dict[str, Any]]): Handshake-опции (shadowtls).
        congestion_control (Optional[str]): Алгоритм congestion control (tuic).
        tag (Optional[str]): Ярлык/метка сервера.
    """
    type: str
    address: str
    port: int
    security: Optional[str] = None
    meta: Dict[str, str] = field(default_factory=dict)
    # Новые поля для поддержки всех протоколов
    uuid: Optional[str] = None
    password: Optional[str] = None
    private_key: Optional[str] = None
    peer_public_key: Optional[str] = None
    pre_shared_key: Optional[str] = None
    local_address: Optional[List[str]] = None
    username: Optional[str] = None
    version: Optional[int] = None
    uuid_list: Optional[List[str]] = None
    alpn: Optional[List[str]] = None
    obfs: Optional[Dict[str, Any]] = None
    tls: Optional[Dict[str, Any]] = None
    handshake: Optional[Dict[str, Any]] = None
    congestion_control: Optional[str] = None
    tag: Optional[str] = None

@dataclass
class PipelineContext:
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: Optional[str] = None
    mode: str = "tolerant"  # 'strict' or 'tolerant'
    user_routes: List[Any] = field(default_factory=list)
    exclusions: List[Any] = field(default_factory=list)
    debug_level: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PipelineResult:
    """Результат выполнения пайплайна подписки (fetch → validate → parse → ...).

    Атрибуты:
        config (Any): Результат экспорта (например, JSON-конфиг или список ParsedServer).
        context (PipelineContext): Контекст выполнения пайплайна (trace_id, режим, метаданные и т.д.).
        errors (list): Список ошибок (PipelineError или строки), возникших на любом этапе пайплайна.
        success (bool): Флаг успешности выполнения пайплайна (True — успех, False — были критические ошибки).
    """
    config: Any  # результат экспорта (например, JSON-конфиг)
    context: PipelineContext
    errors: list
    success: bool

class InboundProfile(BaseModel):
    """InboundProfile описывает параметры входящих прокси-интерфейсов для экспорта в конфиг.

    Args:
        type (str): Тип инбаунда (socks, http, tun, tproxy, ssh, dns, reality-inbound, shadowtls и др.).
        listen (str): Адрес для bind (по умолчанию 127.0.0.1).
        port (int): Порт (по умолчанию безопасный нестандартный порт).
        options (dict): Дополнительные параметры (stack, authentication, dns-mode и др.).

    SEC:
        - По умолчанию bind только на localhost (127.0.0.1).
        - Порты по умолчанию: socks=10808, http=off, tun=off, dns=system.
        - Внешний bind (0.0.0.0) только при явном подтверждении.
        - Валидация типа и диапазона порта.
    """
    type: Literal['socks', 'http', 'tun', 'tproxy', 'ssh', 'dns', 'reality-inbound', 'shadowtls']
    listen: str = Field(default="127.0.0.1", description="Адрес для bind, по умолчанию localhost.")
    port: Optional[int] = Field(default=None, description="Порт, по умолчанию безопасный для типа.")
    options: Optional[dict] = Field(default_factory=dict, description="Дополнительные параметры.")

    @field_validator('listen')
    def validate_listen(cls, v):
        if v not in ("127.0.0.1", "::1") and not v.startswith("192.168."):
            raise ValueError("Bind address must be localhost or private network unless explicitly allowed.")
        return v
    @field_validator('port')
    def validate_port(cls, v, values):
        if v is None:
            return v
        if not (1024 <= v <= 65535):
            raise ValueError("Port must be in 1024-65535 range.")
        return v

class ClientProfile(BaseModel):
    """ClientProfile описывает профиль клиента для экспорта (inbounds, режимы, опции).

    Args:
        inbounds (List[InboundProfile]): Список инбаундов для генерации.
        dns_mode (str): Режим работы DNS (system, tunnel, off).
        extra (dict): Дополнительные параметры профиля.
    """
    inbounds: List[InboundProfile] = Field(default_factory=list, description="Список инбаундов.")
    dns_mode: Optional[str] = Field(default="system", description="Режим работы DNS.")
    extra: Optional[dict] = Field(default_factory=dict, description="Дополнительные параметры профиля.") 