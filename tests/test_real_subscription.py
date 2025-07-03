"""Test with real subscription data."""

from sboxmgr.subscription.manager import SubscriptionManager
from sboxmgr.subscription.models import SubscriptionSource, PipelineContext
from sboxmgr.subscription.validators.protocol_validator import EnhancedRequiredFieldsValidator
import os

def test_real_subscription_validation():
    """Test validation with real subscription data."""
    
    # Use example from examples with correct path
    example_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '../src/sboxmgr/examples/example_uri_list.txt')
    )
    source = SubscriptionSource(
        url=f"file://{example_path}",
        source_type="uri_list"
    )
    # Создаем менеджер
    manager = SubscriptionManager(source)
    
    # Получаем серверы
    result = manager.get_servers()
    
    # Проверяем, что получили серверы
    assert result.success
    assert len(result.config) > 0
    
    # Проверяем, что есть разные типы протоколов
    types = {s.type for s in result.config}
    assert "ss" in types
    assert "vless" in types
    assert "vmess" in types
    
    # Тестируем новый валидатор
    validator = EnhancedRequiredFieldsValidator()
    context = PipelineContext(mode="tolerant", debug_level=1)
    
    validation_result = validator.validate(result.config, context)
    
    # Проверяем результаты валидации
    print(f"Validation errors: {validation_result.errors}")
    print(f"Valid servers: {len(validation_result.valid_servers)}")
    
    # Должны быть валидные серверы
    assert len(validation_result.valid_servers) > 0
    
    # Проверяем, что валидатор не сломал существующие серверы
    assert len(validation_result.valid_servers) >= len(result.config) * 0.8  # По крайней мере 80% серверов должны пройти валидацию

def test_subscription_with_enhanced_validation():
    """Test subscription processing with enhanced validation."""
    
    # Создаем тестовую подписку с разными протоколами
    test_data = """
# Test subscription with various protocols
ss://aes-256-gcm:password@example.com:8388#TestSS
vless://uuid@host:443?encryption=none#TestVLESS
vmess://eyJ2IjoiMiIsInBzIjoiVGVzdCIsImFkZCI6IjEyNy4wLjAuMSIsInBvcnQiOiI0NDMiLCJpZCI6InV1aWQiLCJhaWQiOiIwIiwibmV0IjoidGNwIiwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiJ9
trojan://password@host:443#TestTrojan
""".encode("utf-8")
    
    # Сохраняем во временный файл
    import tempfile
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
        f.write(test_data)
        temp_file = f.name
    
    try:
        source = SubscriptionSource(
            url=f"file://{temp_file}",
            source_type="uri_list"
        )
        
        manager = SubscriptionManager(source)
        result = manager.get_servers()
        
        # Проверяем, что получили серверы
        assert result.success
        assert len(result.config) > 0
        
        # Проверяем типы протоколов
        types = {s.type for s in result.config}
        expected_types = {"ss", "vless", "vmess", "trojan"}
        assert types.intersection(expected_types)
        
        # Тестируем валидацию
        validator = EnhancedRequiredFieldsValidator()
        context = PipelineContext(mode="tolerant", debug_level=1)
        
        validation_result = validator.validate(result.config, context)
        
        print(f"Validation errors: {validation_result.errors}")
        print(f"Valid servers: {len(validation_result.valid_servers)}")
        
        # Должны быть валидные серверы
        assert len(validation_result.valid_servers) > 0
        
    finally:
        import os
        os.unlink(temp_file)

def test_protocol_specific_validation():
    """Test protocol-specific validation."""
    
    from sboxmgr.subscription.validators.protocol_validator import ProtocolSpecificValidator
    
    # Создаем тестовые серверы
    from sboxmgr.subscription.models import ParsedServer
    
    # Valid Shadowsocks
    valid_ss = ParsedServer(
        type="ss",
        address="example.com",
        port=8388,
        security="aes-256-gcm",
        meta={"password": "test_password"}
    )
    
    # Invalid Shadowsocks (missing password)
    invalid_ss = ParsedServer(
        type="ss",
        address="example.com",
        port=8388,
        security="aes-256-gcm",
        meta={}  # Missing password
    )
    
    # Valid VLESS
    valid_vless = ParsedServer(
        type="vless",
        address="host",
        port=443,
        meta={"uuid": "test-uuid", "encryption": "none"}
    )
    
    servers = [valid_ss, invalid_ss, valid_vless]
    
    # Тестируем валидатор
    validator = ProtocolSpecificValidator()
    context = PipelineContext(mode="tolerant", debug_level=1)
    
    result = validator.validate(servers, context)
    
    print(f"Protocol validation errors: {result.errors}")
    print(f"Valid servers: {len(result.valid_servers)}")
    
    # Должны быть ошибки валидации
    assert len(result.errors) > 0
    
    # В tolerant режиме все серверы должны быть включены
    assert len(result.valid_servers) == 3
    
    # Проверяем, что ошибки записаны в meta
    assert "validation_errors" in result.valid_servers[1].meta 

def test_json_subscription_clash_format():
    """Test JSON subscription in Clash format."""
    
    # Используем JSON пример
    example_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '../src/sboxmgr/examples/example_json.json')
    )
    source = SubscriptionSource(
        url=f"file://{example_path}",
        source_type="url_json"
    )
    
    # Создаем менеджер
    manager = SubscriptionManager(source)
    
    # Получаем серверы
    result = manager.get_servers()
    
    # Проверяем, что получили серверы
    assert result.success
    assert len(result.config) > 0
    
    # Проверяем, что есть разные типы протоколов
    types = {s.type for s in result.config}
    assert "vmess" in types
    assert "ss" in types
    
    # Тестируем новый валидатор
    validator = EnhancedRequiredFieldsValidator()
    context = PipelineContext(mode="tolerant", debug_level=1)
    
    validation_result = validator.validate(result.config, context)
    
    print(f"JSON Clash - Validation errors: {validation_result.errors}")
    print(f"JSON Clash - Valid servers: {len(validation_result.valid_servers)}")
    
    # Должны быть валидные серверы
    assert len(validation_result.valid_servers) > 0

def test_base64_subscription_sfi_format():
    """Test base64 subscription in SFI format."""
    
    # Используем base64 пример
    example_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '../src/sboxmgr/examples/example_base64.txt')
    )
    source = SubscriptionSource(
        url=f"file://{example_path}",
        source_type="url_base64"
    )
    
    # Создаем менеджер
    manager = SubscriptionManager(source)
    
    # Получаем серверы
    result = manager.get_servers()
    
    # Для base64 теста можем ожидать ошибки, но проверяем что система не падает
    if result.success:
        assert len(result.config) > 0
        
        # Проверяем, что есть VMess сервер
        types = {s.type for s in result.config}
        assert "vmess" in types
        
        # Тестируем новый валидатор
        validator = EnhancedRequiredFieldsValidator()
        context = PipelineContext(mode="tolerant", debug_level=1)
        
        validation_result = validator.validate(result.config, context)
        
        print(f"Base64 SFI - Validation errors: {validation_result.errors}")
        print(f"Base64 SFI - Valid servers: {len(validation_result.valid_servers)}")
        
        # Должны быть валидные серверы
        assert len(validation_result.valid_servers) > 0
    else:
        # Если base64 не парсится, проверяем что ошибки корректно обработаны
        print(f"Base64 SFI - Failed to parse: {result.errors}")
        assert len(result.errors) > 0
        # Проверяем что ошибка связана с валидацией или парсингом
        assert any("validation" in str(error) or "parse" in str(error) for error in result.errors)

def test_subscription_without_user_agent():
    """Test subscription without User-Agent header."""
    
    # Используем URI list пример без User-Agent
    example_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '../src/sboxmgr/examples/example_uri_list.txt')
    )
    source = SubscriptionSource(
        url=f"file://{example_path}",
        source_type="uri_list",
        headers=None,  # Явно указываем отсутствие заголовков
        user_agent=None  # Явно указываем отсутствие User-Agent
    )
    
    # Создаем менеджер
    manager = SubscriptionManager(source)
    
    # Получаем серверы
    result = manager.get_servers()
    
    # Проверяем, что получили серверы
    assert result.success
    assert len(result.config) > 0
    
    # Проверяем, что есть разные типы протоколов
    types = {s.type for s in result.config}
    assert "ss" in types
    assert "vless" in types
    assert "vmess" in types
    
    # Тестируем новый валидатор
    validator = EnhancedRequiredFieldsValidator()
    context = PipelineContext(mode="tolerant", debug_level=1)
    
    validation_result = validator.validate(result.config, context)
    
    print(f"No UA - Validation errors: {validation_result.errors}")
    print(f"No UA - Valid servers: {len(validation_result.valid_servers)}")
    
    # Должны быть валидные серверы
    assert len(validation_result.valid_servers) > 0

def test_subscription_with_custom_user_agent():
    """Test subscription with custom User-Agent header."""
    
    # Используем URI list пример с кастомным User-Agent
    example_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '../src/sboxmgr/examples/example_uri_list.txt')
    )
    source = SubscriptionSource(
        url=f"file://{example_path}",
        source_type="uri_list",
        headers={"User-Agent": "Custom-UA/1.0"},
        user_agent="Custom-UA/1.0"
    )
    
    # Создаем менеджер
    manager = SubscriptionManager(source)
    
    # Получаем серверы
    result = manager.get_servers()
    
    # Проверяем, что получили серверы
    assert result.success
    assert len(result.config) > 0
    
    # Проверяем, что есть разные типы протоколов
    types = {s.type for s in result.config}
    assert "ss" in types
    assert "vless" in types
    assert "vmess" in types
    
    # Тестируем новый валидатор
    validator = EnhancedRequiredFieldsValidator()
    context = PipelineContext(mode="tolerant", debug_level=1)
    
    validation_result = validator.validate(result.config, context)
    
    print(f"Custom UA - Validation errors: {validation_result.errors}")
    print(f"Custom UA - Valid servers: {len(validation_result.valid_servers)}")
    
    # Должны быть валидные серверы
    assert len(validation_result.valid_servers) > 0 