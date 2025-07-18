"""Subscription parsers package.

Contains concrete parsers that understand different subscription payload
formats such as base64-encoded lines, Clash YAML, raw JSON, URI lists, etc.
All parser classes are registered via the `sboxmgr.subscription.registry`
`@register` decorator so they can be discovered dynamically.
"""

from .base64_parser import *  # noqa: F403
from .clash_parser import *  # noqa: F403
from .json_parser import *  # noqa: F403
from .sfiparser import *  # noqa: F403
from .uri_list_parser import *  # noqa: F403
