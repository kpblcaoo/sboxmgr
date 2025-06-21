"""
Fetchers: загрузчики подписок (HTTP, file, API и др.)

Точка подключения для AuthHandler и HeaderPlugin (будущее).
"""

from .base64_fetcher import *
from .file_fetcher import *
from .json_fetcher import *
from .uri_list_fetcher import * 