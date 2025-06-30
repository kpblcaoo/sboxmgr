```python
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Union, Annotated
from enum import Enum

# Общие типы
class LogLevel(str, Enum):
    """Уровни логирования для клиентов."""
    trace = "trace"
    debug = "debug"
    info = "info"
    warn = "warn"
    error = "error"
    fatal = "fatal"
    panic = "panic"

class DomainStrategy(str, Enum):
    """Стратегия разрешения доменов."""
    prefer_ipv4 = "prefer_ipv4"
    prefer_ipv6 = "prefer_ipv6"
    ipv4_only = "ipv4_only"
    ipv6_only = "ipv6_only"

class Network(str, Enum):
    """Тип сети для соединения."""
    tcp = "tcp"
    udp = "udp"
    tcp_udp = "tcp,udp"

# Общие модели
class TlsConfig(BaseModel):
    """Настройки TLS для протоколов."""
    enabled: Optional[bool] = Field(True, description="Включение TLS для соединения.")
    server_name: Optional[str] = Field(None, description="SNI для TLS-соединения.")
    alpn: Optional[List[str]] = Field(None, description="Список ALPN-протоколов (например, h2, http/1.1).")
    min_version: Optional[Literal["1.0", "1.1", "1.2", "1.3"]] = Field(None, description="Минимальная версия TLS.")
    max_version: Optional[Literal["1.0", "1.1", "1.2", "1.3"]] = Field(None, description="Максимальная версия TLS.")
    certificate_path: Optional[str] = Field(None, description="Путь к файлу сертификата.")
    key_path: Optional[str] = Field(None, description="Путь к файлу ключа.")
    certificate: Optional[str] = Field(None, description="Содержимое сертификата в PEM-формате.")
    key: Optional[str] = Field(None, description="Содержимое ключа в PEM-формате.")
    allow_insecure: Optional[bool] = Field(False, description="Разрешить небезопасные соединения (не рекомендуется).")
    ech: Optional[Dict[str, Any]] = Field(None, description="Настройки ECH для защиты SNI.")
    utls: Optional[Dict[str, Any]] = Field(None, description="Настройки uTLS для имитации TLS-клиента.")

    class Config:
        extra = "forbid"

class StreamSettings(BaseModel):
    """Настройки транспортного уровня."""
    network: Optional[Literal["tcp", "udp", "ws", "http", "grpc", "quic"]] = Field(None, description="Тип транспорта (TCP, WebSocket, gRPC и т.д.).")
    security: Optional[Literal["none", "tls", "reality"]] = Field(None, description="Тип шифрования (TLS, REALITY или none).")
    tls_settings: Optional[TlsConfig] = Field(None, description="Настройки TLS для транспорта.")
    ws_settings: Optional[Dict[str, Any]] = Field(None, description="Настройки WebSocket (path, headers).")
    http_settings: Optional[Dict[str, Any]] = Field(None, description="Настройки HTTP/2 (path, host).")
    grpc_settings: Optional[Dict[str, Any]] = Field(None, description="Настройки gRPC (serviceName).")
    quic_settings: Optional[Dict[str, Any]] = Field(None, description="Настройки QUIC.")

    class Config:
        extra = "forbid"

class MultiplexConfig(BaseModel):
    """Настройки мультиплексирования."""
    enabled: Optional[bool] = Field(None, description="Включение мультиплексирования.")
    protocol: Optional[Literal["smux", "yamux", "h2mux"]] = Field(None, description="Протокол мультиплексирования.")
    max_connections: Optional[int] = Field(None, ge=1, description="Максимальное количество соединений.")
    min_streams: Optional[int] = Field(None, ge=0, description="Минимальное количество потоков.")
    max_streams: Optional[int] = Field(None, ge=0, description="Максимальное количество потоков.")
    padding: Optional[bool] = Field(None, description="Включение padding для обфускации.")

    class Config:
        extra = "forbid"

# Shadowsocks
class ShadowsocksConfig(BaseModel):
    """Конфигурация Shadowsocks для SOCKS5-прокси."""
    server: str = Field(..., description="Адрес сервера (IP или домен).")
    server_port: int = Field(..., ge=1, le=65535, description="Порт сервера.")
    local_address: str = Field("127.0.0.1", description="Локальный адрес для прокси.")
    local_port: int = Field(1080, ge=1, le=65535, description="Локальный порт для прокси.")
    password: str = Field(..., description="Пароль для аутентификации.")
    timeout: int = Field(300, ge=0, description="Таймаут соединения в секундах.")
    method: str = Field("aes-256-gcm", description="Метод шифрования (например, aes-256-gcm, chacha20-ietf-poly1305).")
    fast_open: bool = Field(False, description="Включение TCP Fast Open для ускорения соединения.")
    plugin: Optional[str] = Field(None, description="Плагин обфускации (например, v2ray-plugin).")
    plugin_opts: Optional[Dict[str, Any]] = Field(None, description="Параметры плагина обфускации.")
    udp: Optional[bool] = Field(True, description="Включение UDP-трафика.")

    class Config:
        extra = "forbid"

    @field_validator("method")
    def validate_method(cls, v):
        """Проверка допустимых методов шифрования."""
        valid_methods = ["aes-256-gcm", "chacha20-ietf-poly1305", "aes-128-gcm"]
        if v not in valid_methods:
            raise ValueError(f"Invalid encryption method: {v}")
        return v

# VMess
class VmessUser(BaseModel):
    """Пользователь для VMess-протокола."""
    id: str = Field(..., description="UUID пользователя для аутентификации.")
    alterId: int = Field(0, ge=0, le=65535, description="Количество альтернативных ID (0-65535).")
    security: Optional[Literal["auto", "aes-128-gcm", "chacha20-poly1305", "none"]] = Field("auto", description="Метод шифрования.")
    level: int = Field(0, ge=0, description="Уровень пользователя для политики доступа.")
    email: Optional[str] = Field(None, description="Email для идентификации в логах.")

    class Config:
        extra = "forbid"

class VmessSettings(BaseModel):
    """Настройки VMess-протокола."""
    clients: List[VmessUser] = Field(..., description="Список пользователей для аутентификации.")
    detour: Optional[str] = Field(None, description="Тег для перенаправления соединения.")
    disableInsecureEncryption: bool = Field(False, description="Запрет небезопасных методов шифрования.")

    class Config:
        extra = "forbid"

class VmessConfig(BaseModel):
    """Конфигурация VMess для V2Ray/Xray."""
    server: str = Field(..., description="Адрес сервера (IP или домен).")
    server_port: int = Field(..., ge=1, le=65535, description="Порт сервера.")
    settings: VmessSettings = Field(..., description="Настройки пользователей и политики.")
    streamSettings: StreamSettings = Field(..., description="Настройки транспортного уровня (TCP, WS, gRPC).")
    multiplex: Optional[MultiplexConfig] = Field(None, description="Настройки мультиплексирования.")
    udp: Optional[bool] = Field(True, description="Включение UDP-трафика.")

    class Config:
        extra = "forbid"

# VLESS
class VlessUser(BaseModel):
    """Пользователь для VLESS-протокола."""
    id: str = Field(..., description="UUID пользователя для аутентификации.")
    level: int = Field(0, ge=0, description="Уровень пользователя для политики доступа.")
    email: Optional[str] = Field(None, description="Email для идентификации в логах.")
    flow: Optional[Literal["xtls-rprx-vision", "xtls-rprx-direct"]] = Field(None, description="Тип потока для XTLS.")

    class Config:
        extra = "forbid"

class VlessSettings(BaseModel):
    """Настройки VLESS-протокола."""
    clients: List[VlessUser] = Field(..., description="Список пользователей для аутентификации.")
    decryption: str = Field("none", description="Метод дешифрования (должен быть 'none').")
    fallbacks: Optional[List[Dict[str, Any]]] = Field(None, description="Список fallback-адресов для перенаправления.")

    class Config:
        extra = "forbid"

class VlessConfig(BaseModel):
    """Конфигурация VLESS для Xray."""
    server: str = Field(..., description="Адрес сервера (IP или домен).")
    server_port: int = Field(..., ge=1, le=65535, description="Порт сервера.")
    settings: VlessSettings = Field(..., description="Настройки пользователей и fallback.")
    streamSettings: StreamSettings = Field(..., description="Настройки транспортного уровня (TCP, WS, gRPC).")
    multiplex: Optional[MultiplexConfig] = Field(None, description="Настройки мультиплексирования.")
    udp: Optional[bool] = Field(True, description="Включение UDP-трафика.")

    class Config:
        extra = "forbid"

# Trojan
class TrojanUser(BaseModel):
    """Пользователь для Trojan-протокола."""
    password: str = Field(..., description="Пароль для аутентификации.")

    class Config:
        extra = "forbid"

class TrojanConfig(BaseModel):
    """Кон6
фигурация Trojan для TLS-прокси."""
    server: str = Field(..., description="Адрес сервера (IP или домен).")
    server_port: int = Field(..., ge=1, le=65535, description="Порт сервера.")
    password: str = Field(..., description="Пароль для аутентификации.")
    tls: TlsConfig = Field(..., description="Настройки TLS для соединения.")
    multiplex: Optional[MultiplexConfig] = Field(None, description="Настройки мультиплексирования.")
    udp: Optional[bool] = Field(True, description="Включение UDP-трафика.")
    fallback: Optional[Dict[str, Any]] = Field(None, description="Fallback-адрес для перенаправления.")

    class Config:
        extra = "forbid"

# WireGuard
class WireGuardPeer(BaseModel):
    """Пир для WireGuard-протокола."""
    public_key: str = Field(..., description="Публичный ключ пира.")
    allowed_ips: List[str] = Field(..., description="Разрешённые IP-адреса для маршрутизации.")
    endpoint: Optional[str] = Field(None, description="Адрес пира (IP:порт).")
    persistent_keepalive: Optional[int] = Field(None, ge=0, description="Интервал keepalive в секундах.")
    pre_shared_key: Optional[str] = Field(None, description="Предварительно общий ключ для аутентификации.")

    class Config:
        extra = "forbid"

class WireGuardInterface(BaseModel):
    """Интерфейс для WireGuard-протокола."""
    private_key: str = Field(..., description="Приватный ключ интерфейса.")
    listen_port: Optional[int] = Field(None, ge=1, le=65535, description="Порт для прослушивания.")
    fwmark: Optional[int] = Field(None, ge=0, description="Маркер для маршрутизации.")
    address: Optional[List[str]] = Field(None, description="IP-адреса интерфейса.")
    mtu: Optional[int] = Field(0, ge=0, description="Максимальный размер пакета (0 для автоопределения).")
    dns: Optional[List[str]] = Field(None, description="DNS-серверы для интерфейса.")

    class Config:
        extra = "forbid"

class WireGuardConfig(BaseModel):
    """Конфигурация WireGuard для VPN."""
    interface: WireGuardInterface = Field(..., description="Настройки интерфейса WireGuard.")
    peers: List[WireGuardPeer] = Field(..., description="Список пиров для соединения.")
    udp: Optional[bool] = Field(True, description="Включение UDP-трафика.")

    class Config:
        extra = "forbid"

# OpenVPN
class OpenVPNConfig(BaseModel):
    """Конфигурация OpenVPN для VPN."""
    server: str = Field(..., description="Адрес сервера (IP или домен).")
    port: int = Field(..., ge=1, le=65535, description="Порт сервера.")
    proto: Literal["udp", "tcp"] = Field("udp", description="Протокол соединения (UDP или TCP).")
    dev: Literal["tun", "tap"] = Field("tun", description="Тип устройства (TUN или TAP).")
    ca: str = Field(..., description="Содержимое CA-сертификата в PEM-формате.")
    cert: str = Field(..., description="Содержимое клиентского сертификата в PEM-формате.")
    key: str = Field(..., description="Содержимое клиентского ключа в PEM-формате.")
    dh: Optional[str] = Field(None, description="Содержимое Diffie-Hellman параметров в PEM-формате.")
    topology: Literal["subnet", "net30", "p2p"] = Field("subnet", description="Тип топологии сети.")
    server_address: str = Field("10.8.0.0 255.255.255.0", description="Виртуальный IP-диапазон сервера.")
    push: List[str] = Field(default_factory=list, description="Директивы push для клиентов (например, route).")
    comp_lzo: bool = Field(True, description="Включение сжатия LZO.")
    persist_key: bool = Field(True, description="Сохранение ключа при переподключении.")
    persist_tun: bool = Field(True, description="Сохранение TUN/TAP при переподключении.")
    status: str = Field("openvpn-status.log", description="Путь к файлу статуса.")
    verb: int = Field(3, ge=0, le=11, description="Уровень логирования (0-11).")
    cipher: Optional[Literal["AES-256-GCM", "AES-128-GCM", "CHACHA20-POLY1305"]] = Field(None, description="Шифр для данных.")
    auth: Optional[Literal["SHA1", "SHA256", "SHA512"]] = Field(None, description="Алгоритм аутентификации.")

    class Config:
        extra = "forbid"

    @field_validator("push")
    def validate_push(cls, v):
        """Проверка формата push-директив."""
        for directive in v:
            if not directive.startswith(("route ", "dhcp-option ")):
                raise ValueError(f"Invalid push directive: {directive}")
        return v
```