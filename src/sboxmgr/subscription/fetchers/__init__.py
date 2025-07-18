"""Fetchers: загрузчики подписок (HTTP, file, API и др.).

Точка подключения для AuthHandler и HeaderPlugin (будущее).
"""

from .apifetcher import *
from .file_fetcher import *
from .json_fetcher import *
from .url_fetcher import *
