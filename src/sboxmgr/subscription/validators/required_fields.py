"""Required fields validator for parsed servers.

This module provides validation for essential server configuration fields.
It ensures that all parsed servers have the minimum required fields (type,
address, port) and validates field values for consistency and security
before configuration export.
"""
import re
from .base import BaseParsedValidator, register_parsed_validator, ValidationResult
from sboxmgr.subscription.models import PipelineContext

@register_parsed_validator("required_fields")
class RequiredFieldsValidator(BaseParsedValidator):
    """Validates required fields for ParsedServer: type, address, port, and value acceptability.
    
    This validator ensures that all parsed servers have the essential fields
    required for configuration export. It checks for type, address, and port
    fields and validates their values are within acceptable ranges.
    
    Enhanced to ensure servers have at least one identifier (address, tag, or name)
    and can automatically fix missing identifiers with proper logging.
    """
    
    def validate(self, servers: list, context: PipelineContext) -> ValidationResult:
        """Validate that servers have all required fields with valid values.
        
        Checks each server for required fields (type, address, port) and validates
        that field values are within acceptable ranges and formats.
        
        Args:
            servers: List of ParsedServer objects to validate.
            context: Pipeline context containing validation settings.
            
        Returns:
            ValidationResult: Contains validation errors and list of valid servers.
        """
        errors = []
        valid_servers = []
        
        # Инициализируем контейнер для логирования исправлений
        context.metadata.setdefault('validation_fixes', [])
        
        for idx, s in enumerate(servers):
            server_errors = []
            server_fixes = []
            
            # Проверяем обязательные поля
            if not hasattr(s, 'type') or not s.type:
                server_errors.append("missing type")
            
            if not hasattr(s, 'port') or not isinstance(s.port, int) or not (1 <= s.port <= 65535):
                server_errors.append(f"invalid port: {getattr(s, 'port', None)}")
            
            # Проверяем наличие хотя бы одного идентификатора
            identifier_check = self._check_identifier(s)
            if not identifier_check['valid']:
                server_errors.append(identifier_check['error'])
            
            # Если есть ошибки, добавляем их
            if server_errors:
                error_msg = f"Server[{idx}]: {'; '.join(server_errors)}"
                errors.append(error_msg)
                
                # В tolerant режиме пытаемся исправить сервер
                if context.mode == 'tolerant':
                    fix_result = self._fix_server_identifier(s, idx)
                    if fix_result['success']:
                        valid_servers.append(s)
                        server_fixes.extend(fix_result['fixes'])
                        
                        # Логируем исправления
                        for fix in fix_result['fixes']:
                            context.metadata['validation_fixes'].append({
                                'server_index': idx,
                                'server_identifier': self._get_server_identifier(s),
                                'fix_type': fix['type'],
                                'severity': fix['severity'],
                                'description': fix['description']
                            })
            else:
                # Проверяем, нужно ли добавить address для серверов с другими идентификаторами
                if context.mode == 'tolerant' and (not hasattr(s, 'address') or not s.address):
                    fix_result = self._fix_server_identifier(s, idx)
                    if fix_result['success']:
                        # Логируем исправления
                        for fix in fix_result['fixes']:
                            context.metadata['validation_fixes'].append({
                                'server_index': idx,
                                'server_identifier': self._get_server_identifier(s),
                                'fix_type': fix['type'],
                                'severity': fix['severity'],
                                'description': fix['description']
                            })
                
                valid_servers.append(s)
        
        return ValidationResult(valid=bool(valid_servers), errors=errors, valid_servers=valid_servers)
    
    def _check_identifier(self, server) -> dict:
        """Проверяет наличие валидного идентификатора у сервера.
        
        Args:
            server: ParsedServer объект
            
        Returns:
            Dict с результатом проверки: {'valid': bool, 'error': str}
        """
        # Проверяем address
        if hasattr(server, 'address') and server.address:
            return {'valid': True, 'error': None}
        
        # Проверяем tag
        if hasattr(server, 'tag') and server.tag:
            # Проверяем допустимые символы в tag
            if not re.match(r'^[\w\-\.]+$', server.tag):
                return {'valid': False, 'error': 'invalid tag format (contains special characters)'}
            return {'valid': True, 'error': None}
        
        # Проверяем name в meta
        if hasattr(server, 'meta') and server.meta:
            name = server.meta.get('name')
            if name:
                return {'valid': True, 'error': None}
        
        return {'valid': False, 'error': 'missing identifier (address, tag, or name)'}
    
    def _fix_server_identifier(self, server, index: int) -> dict:
        """Пытается исправить отсутствующий идентификатор сервера.
        
        Args:
            server: ParsedServer объект
            index: Индекс сервера
            
        Returns:
            Dict с результатом исправления: {'success': bool, 'fixes': list}
        """
        fixes = []
        
        # Если есть tag, используем его как address
        if hasattr(server, 'tag') and server.tag:
            server.address = server.tag
            fixes.append({
                'type': 'tag_to_address',
                'severity': 'info',
                'description': f'Used tag "{server.tag}" as address'
            })
            return {'success': True, 'fixes': fixes}
        
        # Если есть name в meta, используем его как address
        if hasattr(server, 'meta') and server.meta:
            name = server.meta.get('name')
            if name:
                server.address = name
                fixes.append({
                    'type': 'name_to_address',
                    'severity': 'info',
                    'description': f'Used meta.name "{name}" as address'
                })
                return {'success': True, 'fixes': fixes}
        
        # Если есть type, создаем generic identifier
        if hasattr(server, 'type') and server.type:
            server.address = f"{server.type}-server-{index}"
            fixes.append({
                'type': 'generated_address',
                'severity': 'warning',
                'description': f'Generated address "{server.address}" from type and index'
            })
            return {'success': True, 'fixes': fixes}
        
        # Если ничего нет, создаем generic identifier
        server.address = f"unknown-server-{index}"
        fixes.append({
            'type': 'generated_address',
            'severity': 'warning',
            'description': f'Generated generic address "{server.address}"'
        })
        return {'success': True, 'fixes': fixes}
    
    def _get_server_identifier(self, server) -> str:
        """Унифицированный метод получения идентификатора сервера.
        
        Args:
            server: ParsedServer объект
            
        Returns:
            Строка-идентификатор сервера
        """
        # Приоритет: address > tag > name > fallback
        if hasattr(server, 'address') and server.address:
            return str(server.address)
        
        if hasattr(server, 'tag') and server.tag:
            return str(server.tag)
        
        if hasattr(server, 'meta') and server.meta:
            name = server.meta.get('name')
            if name:
                return str(name)
        
        return f"server-{id(server)}" 