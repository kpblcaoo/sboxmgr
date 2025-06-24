from abc import ABC, abstractmethod
from .models import SubscriptionSource
import os
from urllib.parse import urlparse

class BaseAuthHandler(ABC):
    """Interface for generating authentication headers/tokens for protected APIs.
    
    This abstract class defines the interface for authentication handlers
    that can be used with fetchers to access protected subscription endpoints.
    """
    
    @abstractmethod
    def get_auth_headers(self, source: SubscriptionSource) -> dict:
        """Generate authentication headers for the given subscription source.
        
        Args:
            source: The subscription source configuration.
            
        Returns:
            Dictionary containing authentication headers.
            
        Raises:
            NotImplementedError: If called directly on base class.
        """
        pass

class BaseHeaderPlugin(ABC):
    """Interface for adding or modifying HTTP headers.
    
    This abstract class provides the interface for header plugins that can
    modify or add HTTP headers before making requests to subscription endpoints.
    """
    
    @abstractmethod
    def process_headers(self, headers: dict, source: SubscriptionSource) -> dict:
        """Process and modify HTTP headers for the subscription request.
        
        Args:
            headers: Current HTTP headers dictionary.
            source: The subscription source configuration.
            
        Returns:
            Modified headers dictionary.
            
        Raises:
            NotImplementedError: If called directly on base class.
        """
        pass

class BaseFetcher(ABC):
    """Abstract base class for subscription fetcher plugins.
    
    This class provides the interface for fetching subscription data from
    various sources like HTTP URLs, files, APIs, etc. All fetcher plugins
    should inherit from this class and implement the fetch method.
    
    Attributes:
        plugin_type: Plugin type identifier for auto-discovery and filtering.
        SUPPORTED_SCHEMES: Tuple of supported URL schemes.
        source: The subscription source configuration.
        auth_handler: Optional authentication handler.
        header_plugins: List of header processing plugins.
    """
    
    plugin_type = "fetcher"
    SUPPORTED_SCHEMES = ("http", "https", "file")

    def __init__(self, source: SubscriptionSource):
        """Initialize the fetcher with a subscription source.
        
        Args:
            source: The subscription source configuration.
            
        Raises:
            ValueError: If URL scheme is not supported.
        """
        self.source = source
        self.auth_handler: BaseAuthHandler | None = None
        self.header_plugins: list[BaseHeaderPlugin] = []
        self.validate_url_scheme(self.source.url)

    @classmethod
    def validate_url_scheme(cls, url: str):
        """Validate that the URL scheme is supported.
        
        Args:
            url: The URL to validate.
            
        Raises:
            ValueError: If the URL scheme is not supported.
        """
        scheme = urlparse(url).scheme
        if scheme not in cls.SUPPORTED_SCHEMES:
            raise ValueError(f"unsupported scheme: {scheme}")

    @abstractmethod
    def fetch(self) -> bytes:
        """Fetch subscription data from the configured source.
        
        Returns:
            Raw subscription data as bytes.
            
        Raises:
            NotImplementedError: If called directly on base class.
            ConnectionError: If unable to connect to the source.
            ValueError: If the source configuration is invalid.
        """
        pass

    def _get_size_limit(self) -> int:
        """Get the size limit for input data in bytes.
        
        Returns the size limit for subscription data fetching. This can be
        overridden in child classes for specific fetcher types. The limit
        helps ensure fail-tolerance and security by preventing oversized downloads.
        
        Returns:
            Size limit in bytes (default: 2MB).
        """
        env_limit = os.getenv("SBOXMGR_FETCH_SIZE_LIMIT")
        if env_limit:
            try:
                return int(env_limit)
            except Exception:
                pass
        # TODO: добавить чтение из config.toml
        return 2 * 1024 * 1024 