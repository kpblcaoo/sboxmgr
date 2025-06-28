# STAGE 4: JSON Integration & CLI Enhancement (АКТУАЛИЗИРОВАНО ПОД ADR-0001 sbox-common)

## 📊 Статус

**Дата актуализации:** 2025-06-28  
**Ветка:** `feature/stage4-json-integration`  
**Статус:** 🔄 **ПЛАНИРОВАНИЕ**

## 🎯 ЦЕЛИ STAGE 4 (АКТУАЛИЗИРОВАНО ПОД ADR-0001)

### 1. JSON Export Framework (Основная цель)
- **JSON Output Standardization** - стандартизованный JSON output для sboxagent
- **Schema Compliance** - соответствие sbox-common протоколам  
- **Metadata Generation** - генерация метаданных конфигураций
- **Multi-Format Support** - JSON + legacy форматы

### 2. Enhanced CLI for Agent Integration
- **JSON CLI Commands** - команды с JSON output
- **Agent-Ready Interface** - CLI готовый для exec() вызовов
- **Improved Argument Parsing** - лучший парсинг аргументов
- **Error Handling Enhancement** - улучшенная обработка ошибок

### 3. Multi-Client Configuration Support  
- **Clash Exporter Implementation** - полная реализация Clash экспорта
- **Xray Exporter Implementation** - реализация Xray экспорта
- **Mihomo Exporter Implementation** - реализация Mihomo экспорта
- **Client Detection & Validation** - автоопределение клиентов

### 4. Configuration Validation Framework
- **Schema Validation** - валидация против sbox-common схем
- **Client-Specific Validation** - валидация под конкретные клиенты
- **Configuration Testing** - тестирование сгенерированных конфигов
- **Error Reporting** - детальная отчетность об ошибках

## 🔧 СООТВЕТСТВИЕ ADR-0001

### ✅ **sboxmgr Роль: GENERATOR**
- Генерирует конфигурации для всех subbox клиентов
- Выводит JSON в стандартизованном формате
- Остается CLI-only инструментом
- Никаких daemon функций

### ✅ **JSON Interface Protocol**
- Все output в JSON формате для sboxagent
- Соответствие sbox-common схемам
- Метаданные для валидации и отслеживания
- Обратная совместимость с legacy форматами

### ✅ **License Compatibility**  
- Чистая Apache-2.0 лицензия
- Никаких GPL компонентов
- JSON граница с sboxagent (GPL)

## 🏗️ АРХИТЕКТУРА STAGE 4 (АКТУАЛИЗИРОВАНО)

### JSON Export Architecture:
```
src/sboxmgr/export/
├── json/
│   ├── __init__.py          # JSON export package
│   ├── exporter.py          # JSON exporter framework
│   ├── metadata.py          # Metadata generation
│   └── validator.py         # JSON schema validation
├── clients/
│   ├── clash_exporter.py    # Clash configuration export
│   ├── xray_exporter.py     # Xray configuration export
│   └── mihomo_exporter.py   # Mihomo configuration export
└── validation/
    ├── schema_validator.py  # Schema compliance validation
    └── client_validator.py  # Client-specific validation
```

### Enhanced CLI Architecture:
```
src/sboxmgr/cli/
├── commands/
│   ├── generate.py          # Enhanced generate command
│   ├── validate.py          # Validation commands
│   └── export.py            # Export commands
├── json/
│   ├── __init__.py          # JSON CLI support
│   ├── formatter.py         # JSON output formatting
│   └── parser.py            # JSON argument parsing
└── utils/
    ├── client_detection.py  # Client detection utilities
    └── error_handling.py    # Enhanced error handling
```

## 📋 ДЕТАЛЬНЫЙ ПЛАН (АКТУАЛИЗИРОВАНО)

### Phase 1: JSON Export Framework (3-4 дня)

#### 1.1 JSON Exporter Implementation
- [ ] Создать `src/sboxmgr/export/json/exporter.py`
- [ ] Стандартизованный JSON output format
- [ ] Metadata generation (source, timestamp, checksum)
- [ ] Schema compliance validation

#### 1.2 Multi-Client JSON Support
- [ ] JSON wrapper для всех экспортеров
- [ ] Client-specific metadata
- [ ] Unified JSON structure
- [ ] Version compatibility tracking

#### 1.3 Schema Integration
- [ ] Интеграция с sbox-common схемами
- [ ] JSON schema validation
- [ ] Error reporting enhancement
- [ ] Compliance checking

### Phase 2: Enhanced CLI Commands (2-3 дня)

#### 2.1 JSON CLI Commands
- [ ] `sboxmgr generate --output json` command
- [ ] `sboxmgr validate --schema` command
- [ ] `sboxmgr export --client [sing-box|clash|xray|mihomo]` command
- [ ] JSON output formatting options

#### 2.2 Agent-Ready Interface
- [ ] Structured JSON output for all commands
- [ ] Exit codes standardization
- [ ] Error JSON format
- [ ] Success JSON format

### Phase 3: Multi-Client Exporters (3-4 дня)

#### 3.1 Clash Exporter Enhancement
- [ ] Полная реализация `ClashExporter`
- [ ] Clash-specific configuration generation
- [ ] Proxy groups и rules generation
- [ ] YAML output support

#### 3.2 Xray Exporter Implementation
- [ ] Создать `XrayExporter` class
- [ ] Xray-specific configuration
- [ ] Protocol compatibility
- [ ] JSON configuration format

#### 3.3 Mihomo Exporter Implementation
- [ ] Создать `MihomoExporter` class
- [ ] Mihomo-specific features
- [ ] Clash compatibility mode
- [ ] Enhanced features support

### Phase 4: Validation Framework (2 дня)

#### 4.1 Configuration Validation
- [ ] Schema-based validation
- [ ] Client-specific validation rules
- [ ] Configuration testing
- [ ] Validation reporting

#### 4.2 Integration Testing
- [ ] End-to-end JSON pipeline testing
- [ ] Multi-client export testing
- [ ] CLI integration testing
- [ ] Error handling testing

## 🔧 ТЕХНИЧЕСКИЕ ТРЕБОВАНИЯ

### JSON Export Framework
```python
# src/sboxmgr/export/json/exporter.py
class JSONExporter:
    def __init__(self):
        self.validator = SchemaValidator()
        self.metadata_generator = MetadataGenerator()
    
    def export_config(self, client_type: str, config_data: dict, 
                     subscription_url: str = None) -> dict:
        """Export configuration in sbox-common format"""
        exported = {
            "client": client_type,
            "version": self._get_client_version(client_type),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "config": config_data,
            "metadata": self._generate_metadata(subscription_url)
        }
        
        # Validate against sbox-common schema
        self.validator.validate(exported, f"{client_type}.schema.json")
        return exported
```

### Enhanced CLI Commands
```python
# src/sboxmgr/cli/commands/generate.py
@app.command()
def generate(
    subscription_url: str,
    client: str = typer.Option("sing-box", help="Target client"),
    output_format: str = typer.Option("json", help="Output format"),
    validate_schema: bool = typer.Option(True, help="Validate against schema")
):
    """Generate configuration with JSON export"""
    try:
        # Generate configuration
        config_data = generator.generate_config(subscription_url, client)
        
        if output_format == "json":
            # Export as JSON with metadata
            result = json_exporter.export_config(client, config_data, subscription_url)
            
            if validate_schema:
                validation = validator.validate_config(result, client)
                if not validation.success:
                    raise ValidationError(validation.errors)
            
            print(json.dumps(result, indent=2))
        else:
            # Legacy format support
            print(legacy_exporter.export(config_data, output_format))
            
    except Exception as e:
        error_response = {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        print(json.dumps(error_response), file=sys.stderr)
        raise typer.Exit(1)
```

### Multi-Client Support
```python
# src/sboxmgr/export/clients/client_factory.py
class ClientExporterFactory:
    def __init__(self):
        self.exporters = {
            "sing-box": SingBoxExporter(),
            "clash": ClashExporter(), 
            "xray": XrayExporter(),
            "mihomo": MihomoExporter()
        }
    
    def get_exporter(self, client_type: str) -> BaseExporter:
        if client_type not in self.exporters:
            raise UnsupportedClientError(f"Unsupported client: {client_type}")
        return self.exporters[client_type]
    
    def get_supported_clients(self) -> List[str]:
        return list(self.exporters.keys())
```

## 🧪 ТЕСТИРОВАНИЕ

### JSON Export Tests:
- [ ] JSON format validation
- [ ] Schema compliance testing
- [ ] Metadata generation testing
- [ ] Multi-client JSON output

### CLI Enhancement Tests:
- [ ] JSON command output testing
- [ ] Error handling testing
- [ ] Agent integration testing
- [ ] Backward compatibility testing

### Multi-Client Tests:
- [ ] Clash exporter testing
- [ ] Xray exporter testing  
- [ ] Mihomo exporter testing
- [ ] Cross-client compatibility

## 🔄 ИНТЕГРАЦИЯ С PHASE 2

### Подготовка к sboxagent Integration:
- ✅ **JSON Output Ready** - стандартизованный JSON для sboxagent
- ✅ **CLI Exec Ready** - CLI готов для exec() вызовов
- ✅ **Multi-Client Support** - поддержка всех subbox клиентов
- ✅ **Schema Compliance** - соответствие sbox-common протоколам

### Connection to Phase 2:
- **sboxagent** будет вызывать `sboxmgr generate --output json`
- **JSON response** будет парситься sboxagent
- **Error handling** через JSON error responses
- **Multi-client** поддержка готова

## 📝 ПРИМЕЧАНИЯ

- Stage 4 фокусируется на подготовке sboxmgr к интеграции с sboxagent
- Все изменения сохраняют CLI-only архитектуру sboxmgr
- JSON interface соответствует ADR-0001
- Подготовка к параллельной реализации Phase 2

## 🎯 ETA: 10-12 дней

**Stage 4 планируется на 10-12 дней** с учетом:
- JSON Export Framework (4 дня)
- Enhanced CLI Commands (3 дня)
- Multi-Client Exporters (4 дня)
- Validation Framework (2 дня)

## 🔗 СВЯЗЬ С ADR-0001

### INTEGRATION PATH B: sboxagent → exec(sboxmgr CLI) → JSON
- ✅ JSON Export Framework → Стандартизованный JSON output
- ✅ Enhanced CLI → Agent-ready interface
- ✅ Multi-Client Support → Все subbox клиенты
- ✅ Schema Compliance → sbox-common integration

---

**Статус**: 🔄 **ПЛАНИРОВАНИЕ АКТУАЛИЗИРОВАНО ПОД ADR-0001**  
**Прогресс**: 0%, планирование завершено  
**Следующий шаг**: Создать ветку feature/stage4-json-integration 