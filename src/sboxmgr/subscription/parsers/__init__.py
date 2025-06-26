"""Subscription parsers package.

Contains concrete parsers that understand different subscription payload
formats such as base64-encoded lines, Clash YAML, raw JSON, URI lists, etc.
All parser classes are registered via the `sboxmgr.subscription.registry`
`@register` decorator so they can be discovered dynamically.
"""
from .clash_parser import *
from .json_parser import *
from .uri_list_parser import *
from .sfiparser import *
from .base64_parser import * 