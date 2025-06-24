import os
import pytest
from sboxmgr.subscription.models import SubscriptionSource, PipelineContext
from sboxmgr.subscription.manager import SubscriptionManager

EXAMPLES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/sboxmgr/examples'))

def detect_source_type(filename):
    if filename.endswith('.json'):
        return 'url_json'
    if filename.endswith('.txt'):
        # Простейшая эвристика: если есть vless://, vmess://, ss:// — uri_list
        with open(filename, 'r', encoding='utf-8') as f:
            data = f.read(2048)
            if any(proto in data for proto in ("vless://", "vmess://", "trojan://", "ss://")):
                return 'uri_list'
            # Можно добавить base64-эвристику
        return 'uri_list'
    return 'url_base64'  # fallback

@pytest.mark.parametrize("example_file", [
    os.path.join(EXAMPLES_DIR, f) for f in os.listdir(EXAMPLES_DIR) if os.path.isfile(os.path.join(EXAMPLES_DIR, f))
])
def test_example_smoke(example_file):
    """Smoke/edge тест: проверяет, что каждый пример из examples/ корректно обрабатывается пайплайном (или ошибка корректно накапливается)."""
    source_type = detect_source_type(example_file)
    source = SubscriptionSource(url='file://' + os.path.abspath(example_file), source_type=source_type)
    mgr = SubscriptionManager(source)
    context = PipelineContext(mode='tolerant')
    result = mgr.get_servers(context=context)
    # Ожидаем либо успех, либо накопленные ошибки (partial_success)
    assert result.success or result.errors
    # Не должно быть необработанных исключений
    if not result.success:
        print(f"[WARN] Example {example_file} errors: {result.errors}") 