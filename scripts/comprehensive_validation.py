#!/usr/bin/env python3
"""
Комплексная валидация всех конфигураций против sing-box.
"""

import os
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
import time

# Добавляем путь к проекту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.sboxmgr.models import *


class ComprehensiveValidator:
    """Комплексный валидатор конфигураций."""
    
    def __init__(self):
        self.configs_dir = Path("tests/data/singbox_configs")
        self.results = {
            'pydantic_validation': {},
            'singbox_validation': {},
            'summary': {}
        }
        self.singbox_path = self.find_singbox_binary()
        
    def find_singbox_binary(self) -> str:
        """Находит путь к sing-box бинарному файлу."""
        possible_paths = [
            "sing-box",
            "/usr/local/bin/sing-box",
            "/usr/bin/sing-box",
            "./sing-box"
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run([path, "version"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print(f"✅ Найден sing-box: {path}")
                    print(f"   Версия: {result.stdout.strip()}")
                    return path
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
                
        print("❌ Sing-box не найден. Установите sing-box для полной валидации.")
        return None
    
    def validate_with_pydantic(self, config: Dict[str, Any], protocol: str) -> Tuple[bool, str]:
        """Валидирует конфигурацию с помощью Pydantic."""
        try:
            # Создаем полную конфигурацию sing-box
            singbox_config = SingBoxConfig(**config)
            
            # Проверяем, что outbound соответствует протоколу
            if singbox_config.outbounds:
                outbound = singbox_config.outbounds[0]
                if hasattr(outbound, 'type') and outbound.type != protocol:
                    return False, f"Тип outbound не соответствует протоколу: {outbound.type} != {protocol}"
                    
            return True, "✅ Pydantic валидация прошла успешно"
            
        except Exception as e:
            return False, f"❌ Pydantic ошибка: {str(e)}"
    
    def validate_with_singbox(self, config: Dict[str, Any], protocol: str) -> Tuple[bool, str]:
        """Валидирует конфигурацию с помощью sing-box."""
        if not self.singbox_path:
            return False, "❌ Sing-box не установлен"
            
        try:
            # Сохраняем конфигурацию во временный файл
            temp_config = Path(f"/tmp/singbox_test_{protocol}.json")
            with open(temp_config, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            # Запускаем sing-box check
            result = subprocess.run(
                [self.singbox_path, "check", "-c", str(temp_config)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Удаляем временный файл
            temp_config.unlink(missing_ok=True)
            
            if result.returncode == 0:
                return True, "✅ Sing-box валидация прошла успешно"
            else:
                return False, f"❌ Sing-box ошибка: {result.stderr.strip()}"
                
        except subprocess.TimeoutExpired:
            return False, "❌ Таймаут валидации"
        except Exception as e:
            return False, f"❌ Ошибка валидации: {str(e)}"
    
    def validate_all_configs(self):
        """Валидирует все конфигурации."""
        if not self.configs_dir.exists():
            print(f"❌ Директория с конфигурациями не найдена: {self.configs_dir}")
            return
            
        config_files = list(self.configs_dir.glob("*_test.json"))
        print(f"🔍 Найдено {len(config_files)} конфигураций для валидации")
        
        for config_file in config_files:
            protocol = config_file.stem.replace("_test", "")
            print(f"\n📋 Валидация {protocol}...")
            
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Pydantic валидация
                pydantic_success, pydantic_message = self.validate_with_pydantic(config, protocol)
                self.results['pydantic_validation'][protocol] = {
                    'success': pydantic_success,
                    'message': pydantic_message
                }
                print(f"   Pydantic: {pydantic_message}")
                
                # Sing-box валидация
                singbox_success, singbox_message = self.validate_with_singbox(config, protocol)
                self.results['singbox_validation'][protocol] = {
                    'success': singbox_success,
                    'message': singbox_message
                }
                print(f"   Sing-box: {singbox_message}")
                
            except Exception as e:
                print(f"   ❌ Ошибка обработки {protocol}: {e}")
                self.results['pydantic_validation'][protocol] = {
                    'success': False,
                    'message': f"Ошибка обработки: {str(e)}"
                }
                self.results['singbox_validation'][protocol] = {
                    'success': False,
                    'message': f"Ошибка обработки: {str(e)}"
                }
    
    def generate_summary(self):
        """Генерирует сводку результатов."""
        total_configs = len(self.results['pydantic_validation'])
        
        pydantic_success = sum(1 for r in self.results['pydantic_validation'].values() if r['success'])
        singbox_success = sum(1 for r in self.results['singbox_validation'].values() if r['success'])
        
        self.results['summary'] = {
            'total_configs': total_configs,
            'pydantic_success': pydantic_success,
            'pydantic_failure': total_configs - pydantic_success,
            'singbox_success': singbox_success,
            'singbox_failure': total_configs - singbox_success,
            'pydantic_coverage': (pydantic_success / total_configs * 100) if total_configs > 0 else 0,
            'singbox_coverage': (singbox_success / total_configs * 100) if total_configs > 0 else 0
        }
    
    def generate_detailed_report(self) -> str:
        """Генерирует детальный отчет."""
        report = []
        report.append("# Детальный отчет валидации конфигураций")
        report.append("")
        report.append(f"Дата: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Сводка
        summary = self.results['summary']
        report.append("## Сводка")
        report.append("")
        report.append(f"- Всего конфигураций: {summary['total_configs']}")
        report.append(f"- Pydantic успешно: {summary['pydantic_success']} ({summary['pydantic_coverage']:.1f}%)")
        report.append(f"- Pydantic неудачно: {summary['pydantic_failure']}")
        report.append(f"- Sing-box успешно: {summary['singbox_success']} ({summary['singbox_coverage']:.1f}%)")
        report.append(f"- Sing-box неудачно: {summary['singbox_failure']}")
        report.append("")
        
        # Детальные результаты
        report.append("## Детальные результаты")
        report.append("")
        report.append("| Протокол | Pydantic | Sing-box | Примечания |")
        report.append("|----------|----------|----------|------------|")
        
        for protocol in sorted(self.results['pydantic_validation'].keys()):
            pydantic_result = self.results['pydantic_validation'][protocol]
            singbox_result = self.results['singbox_validation'][protocol]
            
            pydantic_status = "✅" if pydantic_result['success'] else "❌"
            singbox_status = "✅" if singbox_result['success'] else "❌"
            
            notes = []
            if not pydantic_result['success']:
                notes.append(f"Pydantic: {pydantic_result['message']}")
            if not singbox_result['success']:
                notes.append(f"Sing-box: {singbox_result['message']}")
                
            notes_str = "; ".join(notes) if notes else "Все проверки пройдены"
            
            report.append(f"| {protocol} | {pydantic_status} | {singbox_status} | {notes_str} |")
            
        report.append("")
        
        # Рекомендации
        report.append("## Рекомендации")
        report.append("")
        
        if summary['pydantic_failure'] > 0:
            report.append("### Проблемы с Pydantic моделями:")
            for protocol, result in self.results['pydantic_validation'].items():
                if not result['success']:
                    report.append(f"- **{protocol}**: {result['message']}")
            report.append("")
            
        if summary['singbox_failure'] > 0:
            report.append("### Проблемы с Sing-box валидацией:")
            for protocol, result in self.results['singbox_validation'].items():
                if not result['success']:
                    report.append(f"- **{protocol}**: {result['message']}")
            report.append("")
            
        if summary['pydantic_coverage'] == 100 and summary['singbox_coverage'] == 100:
            report.append("🎉 Все конфигурации прошли валидацию успешно!")
            
        return "\n".join(report)
    
    def save_results(self):
        """Сохраняет результаты в JSON файл."""
        results_file = Path("docs/validation_results.json")
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
            
        print(f"💾 Результаты сохранены в {results_file}")


def main():
    """Основная функция."""
    validator = ComprehensiveValidator()
    
    print("🔍 Комплексная валидация конфигураций sing-box...")
    print("=" * 60)
    
    # Валидируем все конфигурации
    validator.validate_all_configs()
    
    # Генерируем сводку
    validator.generate_summary()
    
    # Сохраняем результаты
    validator.save_results()
    
    # Генерируем отчет
    report = validator.generate_detailed_report()
    
    # Сохраняем отчет
    report_path = "docs/comprehensive_validation_report.md"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
        
    print(f"\n📊 Отчет сохранен в {report_path}")
    print("\n" + "=" * 60)
    print(report)


if __name__ == "__main__":
    main() 