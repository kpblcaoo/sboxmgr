"""DEPRECATED: User models for different protocols.

This module is deprecated and will be removed in a future version.
Use src.sboxmgr.models.singbox.auth instead for authentication models.

This file contains legacy user models that are being replaced by the
authentication models in src/sboxmgr/models/singbox/auth.py.
"""

import warnings

warnings.warn(
    "src.sboxmgr.models.users is deprecated. Use src.sboxmgr.models.singbox.auth instead.",
    DeprecationWarning,
    stacklevel=2
)

"""User models for different protocols."""

from pydantic import BaseModel, Field
from typing import Literal


class SocksUser(BaseModel):
    """SOCKS user configuration."""

    username: str
    password: str


class HttpUser(BaseModel):
    """HTTP user configuration."""

    username: str
    password: str


class VmessUser(BaseModel):
    """VMess user configuration."""

    id: str
    alterId: int = Field(0, ge=0)
    security: Literal["auto", "aes-128-gcm", "chacha20-poly1305", "none"] = "auto"


class VlessUser(BaseModel):
    """VLESS user configuration."""

    id: str
    flow: Literal["xtls-rprx-vision", "xtls-rprx-direct"] = None


class TrojanUser(BaseModel):
    """Trojan user configuration."""

    password: str


class HysteriaUser(BaseModel):
    """Hysteria user configuration."""

    password: str


class TuicUser(BaseModel):
    """TUIC user configuration."""

    uuid: str
    password: str
