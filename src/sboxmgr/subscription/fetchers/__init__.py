"""Fetchers: загрузчики подписок (HTTP, file, API и др.).

Точка подключения для AuthHandler и HeaderPlugin (будущее).
"""

from .apifetcher import *  # noqa: F403
from .file_fetcher import *  # noqa: F403
from .json_fetcher import *  # noqa: F403
from .url_fetcher import *  # noqa: F403
