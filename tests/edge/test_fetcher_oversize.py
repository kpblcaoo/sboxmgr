def test_fetcher_unsupported_protocols():
    """Edge-case: Fetcher должен явно запрещать или безопасно fallback для нестандартных схем."""
    from sboxmgr.subscription.models import SubscriptionSource
    from sboxmgr.subscription.manager import SubscriptionManager
    unsupported = [
        "ftp://example.com/file.txt",
        "data:text/plain;base64,SGVsbG8sIFdvcmxkIQ==",
        "chrome-extension://abcdefg/data.json"
    ]
    for url in unsupported:
        source = SubscriptionSource(url=url, source_type="url_base64")
        try:
            mgr = SubscriptionManager(source)
            mgr.get_servers()
            assert False, f"Fetcher must not support scheme: {url}"
        except Exception as e:
            assert "unsupported" in str(e).lower() or "not allowed" in str(e).lower() or "invalid" in str(e).lower() 