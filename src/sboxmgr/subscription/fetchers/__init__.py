"""
Fetchers: загрузчики подписок (HTTP, file, API и др.)

Точка подключения для AuthHandler и HeaderPlugin (будущее).
"""

from .url_fetcher import *
from .file_fetcher import *
from .json_fetcher import *
from .apifetcher import * 