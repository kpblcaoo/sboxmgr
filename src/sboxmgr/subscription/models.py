from dataclasses import dataclass, field
from typing import Optional, Dict

@dataclass
class SubscriptionSource:
    url: str
    source_type: str  # url_base64, url_json, file_json, uri_list, ...
    headers: Optional[Dict[str, str]] = None
    label: Optional[str] = None

@dataclass
class ParsedServer:
    type: str
    address: str
    port: int
    security: Optional[str] = None
    meta: Dict[str, str] = field(default_factory=dict) 