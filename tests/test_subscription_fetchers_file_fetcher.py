"""Tests for sboxmgr.subscription.fetchers.file_fetcher module."""

import os
import pytest
import tempfile
import threading
from unittest.mock import patch, mock_open

from sboxmgr.subscription.fetchers.file_fetcher import FileFetcher
from sboxmgr.subscription.models import SubscriptionSource


class TestFileFetcher:
    """Test FileFetcher functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        # Clear cache before each test
        FileFetcher._fetch_cache.clear()
    
    def test_file_fetcher_init(self):
        """Test FileFetcher initialization."""
        source = SubscriptionSource(url="file:///path/to/file.txt", source_type="file")
        fetcher = FileFetcher(source)
        
        assert fetcher.source == source
        assert hasattr(fetcher, '_cache_lock')
        assert hasattr(fetcher, '_fetch_cache')
    
    def test_file_fetcher_fetch_success(self):
        """Test successful file fetching."""
        test_content = b"test subscription content"
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(test_content)
            tmp_file_path = tmp_file.name
        
        try:
            source = SubscriptionSource(url=f"file://{tmp_file_path}", source_type="file")
            fetcher = FileFetcher(source)
            
            result = fetcher.fetch()
            
            assert result == test_content
        finally:
            os.unlink(tmp_file_path)
    
    def test_file_fetcher_fetch_with_file_prefix_removal(self):
        """Test file fetching with file:// prefix removal."""
        test_content = b"content with file prefix"
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(test_content)
            tmp_file_path = tmp_file.name
        
        try:
            # Test with file:// prefix
            source = SubscriptionSource(url=f"file://{tmp_file_path}", source_type="file")
            fetcher = FileFetcher(source)
            
            result = fetcher.fetch()
            
            assert result == test_content
        finally:
            os.unlink(tmp_file_path)
    
    def test_file_fetcher_fetch_caching(self):
        """Test file fetching with caching."""
        test_content = b"cached content"
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(test_content)
            tmp_file_path = tmp_file.name
        
        try:
            source = SubscriptionSource(url=f"file://{tmp_file_path}", source_type="file")
            fetcher = FileFetcher(source)
            
            # First fetch
            result1 = fetcher.fetch()
            assert result1 == test_content
            
            # Modify file content
            with open(tmp_file_path, "wb") as f:
                f.write(b"modified content")
            
            # Second fetch should return cached content
            result2 = fetcher.fetch()
            assert result2 == test_content  # Should be cached, not modified
            
            # Verify cache contains the data
            key = (source.url,)
            assert key in FileFetcher._fetch_cache
            assert FileFetcher._fetch_cache[key] == test_content
            
        finally:
            os.unlink(tmp_file_path)
    
    def test_file_fetcher_fetch_force_reload(self):
        """Test file fetching with force reload."""
        test_content = b"original content"
        modified_content = b"modified content"
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(test_content)
            tmp_file_path = tmp_file.name
        
        try:
            source = SubscriptionSource(url=f"file://{tmp_file_path}", source_type="file")
            fetcher = FileFetcher(source)
            
            # First fetch
            result1 = fetcher.fetch()
            assert result1 == test_content
            
            # Modify file content
            with open(tmp_file_path, "wb") as f:
                f.write(modified_content)
            
            # Force reload should get new content
            result2 = fetcher.fetch(force_reload=True)
            assert result2 == modified_content
            
        finally:
            os.unlink(tmp_file_path)
    
    def test_file_fetcher_fetch_size_limit_exceeded(self):
        """Test file fetching when size limit is exceeded."""
        # Create content larger than default limit (2MB)
        large_content = b"x" * (3 * 1024 * 1024)  # 3MB
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(large_content)
            tmp_file_path = tmp_file.name
        
        try:
            source = SubscriptionSource(url=f"file://{tmp_file_path}", source_type="file")
            fetcher = FileFetcher(source)
            
            with pytest.raises(ValueError, match="File size exceeds limit"):
                fetcher.fetch()
                
        finally:
            os.unlink(tmp_file_path)
    
    def test_file_fetcher_fetch_file_not_found(self):
        """Test file fetching when file doesn't exist."""
        source = SubscriptionSource(url="file:///nonexistent/file.txt", source_type="file")
        fetcher = FileFetcher(source)
        
        with pytest.raises(FileNotFoundError):
            fetcher.fetch()
    
    def test_get_size_limit_default(self):
        """Test _get_size_limit with default value."""
        source = SubscriptionSource(url="file:///test.txt", source_type="file")
        fetcher = FileFetcher(source)
        
        limit = fetcher._get_size_limit()
        
        assert limit == 2 * 1024 * 1024  # 2MB default
    
    def test_get_size_limit_from_env_valid(self):
        """Test _get_size_limit with valid environment variable."""
        source = SubscriptionSource(url="file:///test.txt", source_type="file")
        fetcher = FileFetcher(source)
        
        with patch.dict(os.environ, {"SBOXMGR_FETCH_SIZE_LIMIT": "1048576"}):  # 1MB
            limit = fetcher._get_size_limit()
            
        assert limit == 1048576
    
    def test_get_size_limit_from_env_invalid(self):
        """Test _get_size_limit with invalid environment variable."""
        source = SubscriptionSource(url="file:///test.txt", source_type="file")
        fetcher = FileFetcher(source)
        
        with patch.dict(os.environ, {"SBOXMGR_FETCH_SIZE_LIMIT": "invalid"}):
            limit = fetcher._get_size_limit()
            
        assert limit == 2 * 1024 * 1024  # Should fallback to default
    
    def test_get_size_limit_from_env_empty(self):
        """Test _get_size_limit with empty environment variable."""
        source = SubscriptionSource(url="file:///test.txt", source_type="file")
        fetcher = FileFetcher(source)
        
        with patch.dict(os.environ, {"SBOXMGR_FETCH_SIZE_LIMIT": ""}):
            limit = fetcher._get_size_limit()
            
        assert limit == 2 * 1024 * 1024  # Should fallback to default


class TestFileFetcherCaching:
    """Test FileFetcher caching behavior."""
    
    def setup_method(self):
        """Setup test environment."""
        FileFetcher._fetch_cache.clear()
    
    def test_cache_key_generation(self):
        """Test cache key generation."""
        source = SubscriptionSource(url="file:///test.txt", source_type="file")
        fetcher = FileFetcher(source)
        
        # Mock file operations
        with patch("builtins.open", mock_open(read_data=b"test")):
            fetcher.fetch()
            
        key = (source.url,)
        assert key in FileFetcher._fetch_cache
    
    def test_cache_thread_safety(self):
        """Test cache thread safety."""
        test_content = b"thread safety test"
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(test_content)
            tmp_file_path = tmp_file.name
        
        try:
            source = SubscriptionSource(url=f"file://{tmp_file_path}", source_type="file")
            results = []
            errors = []
            
            def fetch_worker():
                try:
                    fetcher = FileFetcher(source)
                    result = fetcher.fetch()
                    results.append(result)
                except Exception as e:
                    errors.append(e)
            
            # Create multiple threads
            threads = []
            for _ in range(10):
                thread = threading.Thread(target=fetch_worker)
                threads.append(thread)
                thread.start()
            
            # Wait for all threads
            for thread in threads:
                thread.join()
            
            # Check results
            assert len(errors) == 0, f"Errors occurred: {errors}"
            assert len(results) == 10
            assert all(result == test_content for result in results)
            
        finally:
            os.unlink(tmp_file_path)
    
    def test_multiple_fetchers_same_url(self):
        """Test multiple fetchers with the same URL share cache."""
        test_content = b"shared cache test"
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(test_content)
            tmp_file_path = tmp_file.name
        
        try:
            source1 = SubscriptionSource(url=f"file://{tmp_file_path}", source_type="file")
            source2 = SubscriptionSource(url=f"file://{tmp_file_path}", source_type="file")
            
            fetcher1 = FileFetcher(source1)
            fetcher2 = FileFetcher(source2)
            
            # First fetcher populates cache
            result1 = fetcher1.fetch()
            
            # Modify file
            with open(tmp_file_path, "wb") as f:
                f.write(b"modified")
            
            # Second fetcher should get cached result
            result2 = fetcher2.fetch()
            
            assert result1 == result2 == test_content
            
        finally:
            os.unlink(tmp_file_path)


class TestFileFetcherEdgeCases:
    """Test edge cases and error conditions."""
    
    def setup_method(self):
        """Setup test environment."""
        FileFetcher._fetch_cache.clear()
    
    def test_fetch_empty_file(self):
        """Test fetching empty file."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            # File is empty by default
            tmp_file_path = tmp_file.name
        
        try:
            source = SubscriptionSource(url=f"file://{tmp_file_path}", source_type="file")
            fetcher = FileFetcher(source)
            
            result = fetcher.fetch()
            
            assert result == b""
            
        finally:
            os.unlink(tmp_file_path)
    
    def test_fetch_binary_file(self):
        """Test fetching binary file."""
        binary_content = bytes(range(256))  # All byte values
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(binary_content)
            tmp_file_path = tmp_file.name
        
        try:
            source = SubscriptionSource(url=f"file://{tmp_file_path}", source_type="file")
            fetcher = FileFetcher(source)
            
            result = fetcher.fetch()
            
            assert result == binary_content
            
        finally:
            os.unlink(tmp_file_path)
    
    def test_fetch_exactly_at_size_limit(self):
        """Test fetching file exactly at size limit."""
        # Set a small size limit for testing
        limit = 1024  # 1KB
        content = b"x" * limit
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            source = SubscriptionSource(url=f"file://{tmp_file_path}", source_type="file")
            fetcher = FileFetcher(source)
            
            with patch.dict(os.environ, {"SBOXMGR_FETCH_SIZE_LIMIT": str(limit)}):
                result = fetcher.fetch()
                
            assert result == content
            
        finally:
            os.unlink(tmp_file_path)
    
    def test_fetch_one_byte_over_limit(self):
        """Test fetching file one byte over limit."""
        limit = 1024  # 1KB
        content = b"x" * (limit + 1)
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            source = SubscriptionSource(url=f"file://{tmp_file_path}", source_type="file")
            fetcher = FileFetcher(source)
            
            with patch.dict(os.environ, {"SBOXMGR_FETCH_SIZE_LIMIT": str(limit)}):
                with pytest.raises(ValueError, match="File size exceeds limit"):
                    fetcher.fetch()
                    
        finally:
            os.unlink(tmp_file_path)
    
    def test_fetch_url_without_file_prefix(self):
        """Test fetching with URL without file:// prefix should fail validation."""
        test_content = b"no prefix test"
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(test_content)
            tmp_file_path = tmp_file.name
        
        try:
            # URL without file:// prefix should fail validation
            source = SubscriptionSource(url=tmp_file_path, source_type="file")
            
            with pytest.raises(ValueError, match="unsupported scheme"):
                FileFetcher(source)
            
        finally:
            os.unlink(tmp_file_path)


class TestFileFetcherIntegration:
    """Integration tests for FileFetcher."""
    
    def setup_method(self):
        """Setup test environment."""
        FileFetcher._fetch_cache.clear()
    
    def test_realistic_subscription_file(self):
        """Test with realistic subscription file content."""
        # Simulate a real subscription file
        subscription_content = b"""
        {
            "servers": [
                {
                    "type": "vless",
                    "server": "example.com",
                    "server_port": 443,
                    "uuid": "12345678-1234-1234-1234-123456789abc"
                }
            ]
        }
        """
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp_file:
            tmp_file.write(subscription_content)
            tmp_file_path = tmp_file.name
        
        try:
            source = SubscriptionSource(url=f"file://{tmp_file_path}", source_type="file")
            fetcher = FileFetcher(source)
            
            result = fetcher.fetch()
            
            assert result == subscription_content
            assert b"vless" in result
            assert b"example.com" in result
            
        finally:
            os.unlink(tmp_file_path)
    
    def test_fetch_with_different_file_extensions(self):
        """Test fetching files with different extensions."""
        test_cases = [
            (".json", b'{"test": "json"}'),
            (".yaml", b"test: yaml"),
            (".txt", b"plain text"),
            (".conf", b"config=value"),
            ("", b"no extension")
        ]
        
        for extension, content in test_cases:
            with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp_file:
                tmp_file.write(content)
                tmp_file_path = tmp_file.name
            
            try:
                source = SubscriptionSource(url=f"file://{tmp_file_path}", source_type="file")
                fetcher = FileFetcher(source)
                
                result = fetcher.fetch()
                
                assert result == content
                
            finally:
                os.unlink(tmp_file_path)