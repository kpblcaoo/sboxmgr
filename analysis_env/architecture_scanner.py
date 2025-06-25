#!/usr/bin/env python3
"""
Продвинутый архитектурный анализатор для sboxmgr
Использует AST, networkx и другие инструменты для глубокого анализа структуры
"""

import ast
import os
import sys
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple, Any
import networkx as nx
import json

class ArchitecturalAnalyzer:
    """Глубокий анализатор архитектуры проекта"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.src_root = self.project_root / "src" / "sboxmgr"
        
        # Результаты анализа
        self.classes = {}  # class_name -> {file, methods, bases, decorators}
        self.functions = {}  # func_name -> {file, calls, args}
        self.imports = defaultdict(set)  # file -> set of imports
        self.dependencies = nx.DiGraph()  # граф зависимостей
        self.interfaces = {}  # интерфейсы/ABC
        self.decorators = defaultdict(list)  # decorator -> [classes/functions]
        self.singletons = []  # классы-синглтоны
        self.factories = []  # фабричные паттерны
        self.di_patterns = []  # паттерны dependency injection
        
    def analyze(self):
        """Запуск полного анализа"""
        print("🔍 Начинаю глубокий архитектурный анализ...")
        
        # Собираем все Python файлы
        python_files = list(self.src_root.rglob("*.py"))
        print(f"📁 Найдено {len(python_files)} Python файлов")
        
        # Анализируем каждый файл
        for py_file in python_files:
            try:
                self._analyze_file(py_file)
            except Exception as e:
                print(f"⚠️  Ошибка в файле {py_file}: {e}")
        
        # Строим граф зависимостей
        self._build_dependency_graph()
        
        # Ищем архитектурные паттерны
        self._detect_patterns()
        
        print("✅ Анализ завершен!")
        
    def _analyze_file(self, file_path: Path):
        """Анализ одного файла через AST"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(file_path))
            
            relative_path = file_path.relative_to(self.project_root)
            visitor = FileVisitor(str(relative_path), self)
            visitor.visit(tree)
            
        except Exception as e:
            print(f"🚨 AST ошибка в {file_path}: {e}")
    
    def _build_dependency_graph(self):
        """Построение графа зависимостей между модулями"""
        for file_path, imports in self.imports.items():
            for imported in imports:
                # Добавляем ребро: file -> imported module
                self.dependencies.add_edge(file_path, imported, type="import")
    
    def _detect_patterns(self):
        """Детектирование архитектурных паттернов"""
        self._detect_singletons()
        self._detect_factories()
        self._detect_di_patterns()
    
    def _detect_singletons(self):
        """Поиск паттерна Singleton"""
        for class_name, class_info in self.classes.items():
            methods = class_info.get('methods', [])
            # Ищем признаки синглтона
            has_instance = any('_instance' in method for method in methods)
            has_default = any('default' in method for method in methods)
            has_get_instance = any('get_instance' in method or 'getInstance' in method for method in methods)
            
            if has_instance or (has_default and has_get_instance):
                self.singletons.append({
                    'class': class_name,
                    'file': class_info['file'],
                    'confidence': 'high' if has_instance else 'medium'
                })
    
    def _detect_factories(self):
        """Поиск фабричных паттернов"""
        for class_name, class_info in self.classes.items():
            methods = class_info.get('methods', [])
            # Ищем фабричные методы
            factory_methods = [m for m in methods if 'create' in m.lower() or 'build' in m.lower() or 'make' in m.lower()]
            
            if factory_methods:
                self.factories.append({
                    'class': class_name,
                    'file': class_info['file'],
                    'methods': factory_methods
                })
    
    def _detect_di_patterns(self):
        """Поиск паттернов Dependency Injection"""
        for class_name, class_info in self.classes.items():
            # Ищем в конструкторах параметры с типами
            init_info = class_info.get('init_params', [])
            
            # Признаки DI: много параметров с типами, Optional параметры
            if len(init_info) > 2:  # больше self и одного обязательного
                optional_params = [p for p in init_info if p.get('optional', False)]
                typed_params = [p for p in init_info if p.get('type_hint')]
                
                if optional_params or len(typed_params) > 1:
                    self.di_patterns.append({
                        'class': class_name,
                        'file': class_info['file'],
                        'injectable_params': len(init_info) - 1,  # минус self
                        'optional_params': len(optional_params),
                        'typed_params': len(typed_params)
                    })
    
    def get_orchestrator_candidates(self) -> List[Dict]:
        """Поиск кандидатов на роль Orchestrator"""
        candidates = []
        
        for class_name, class_info in self.classes.items():
            score = 0
            reasons = []
            
            # Проверяем название
            if 'manager' in class_name.lower() or 'orchestrat' in class_name.lower() or 'facade' in class_name.lower():
                score += 3
                reasons.append("название указывает на центральную роль")
            
            # Проверяем количество методов (много методов = центральная роль?)
            method_count = len(class_info.get('methods', []))
            if method_count > 10:
                score += 2
                reasons.append(f"много методов ({method_count})")
            
            # Проверяем DI паттерны
            di_info = next((di for di in self.di_patterns if di['class'] == class_name), None)
            if di_info:
                score += di_info['injectable_params']
                reasons.append(f"DI паттерн ({di_info['injectable_params']} инъекций)")
            
            # Проверяем наличие export/build методов
            methods = class_info.get('methods', [])
            export_methods = [m for m in methods if 'export' in m.lower() or 'build' in m.lower()]
            if export_methods:
                score += len(export_methods)
                reasons.append(f"методы экспорта/сборки: {export_methods}")
            
            if score >= 3:  # минимальный порог
                candidates.append({
                    'class': class_name,
                    'file': class_info['file'],
                    'score': score,
                    'reasons': reasons,
                    'methods': methods
                })
        
        return sorted(candidates, key=lambda x: x['score'], reverse=True)
    
    def get_missing_components(self, target_schema: Dict) -> Dict:
        """Сравнение с целевой схемой"""
        missing = {
            'classes': [],
            'interfaces': [],
            'patterns': []
        }
        
        # Список ожидаемых компонентов из схемы
        expected_components = [
            'Orchestrator', 'SubscriptionMgr', 'ExportedConfigBuilder',
            'OutboundManager', 'InboundManager', 'RouteManager', 'SafetyGuard',
            'SingboxExporter', 'ClashExporter', 'XrayExporter',
            'UrlFetcher', 'FileFetcher', 'TagFilter', 'EnrichGeo', 'LatencyAnnotator'
        ]
        
        existing_classes = set(self.classes.keys())
        
        for expected in expected_components:
            # Точное совпадение
            if expected not in existing_classes:
                # Проверяем приблизительные совпадения
                similar = [cls for cls in existing_classes if expected.lower() in cls.lower() or cls.lower() in expected.lower()]
                if not similar:
                    missing['classes'].append(expected)
        
        return missing
    
    def generate_report(self) -> Dict:
        """Генерация полного отчета"""
        orchestrator_candidates = self.get_orchestrator_candidates()
        missing_components = self.get_missing_components({})
        
        # Статистика по модулям
        module_stats = {}
        for file_path, imports in self.imports.items():
            module_name = Path(file_path).stem
            classes_in_module = [cls for cls, info in self.classes.items() if info['file'] == file_path]
            
            module_stats[module_name] = {
                'file': file_path,
                'classes': len(classes_in_module),
                'imports': len(imports),
                'class_list': classes_in_module
            }
        
        return {
            'summary': {
                'total_classes': len(self.classes),
                'total_functions': len(self.functions),
                'total_modules': len(self.imports),
                'singletons': len(self.singletons),
                'factories': len(self.factories),
                'di_patterns': len(self.di_patterns)
            },
            'orchestrator_candidates': orchestrator_candidates,
            'missing_components': missing_components,
            'singletons': self.singletons,
            'factories': self.factories,
            'di_patterns': self.di_patterns,
            'module_stats': module_stats,
            'top_classes_by_methods': sorted(
                [(name, len(info.get('methods', []))) for name, info in self.classes.items()],
                key=lambda x: x[1], reverse=True
            )[:10]
        }


class FileVisitor(ast.NodeVisitor):
    """AST visitor для анализа файла"""
    
    def __init__(self, file_path: str, analyzer: ArchitecturalAnalyzer):
        self.file_path = file_path
        self.analyzer = analyzer
        self.current_class = None
    
    def visit_Import(self, node):
        """Обработка import statements"""
        for alias in node.names:
            self.analyzer.imports[self.file_path].add(alias.name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Обработка from X import Y statements"""
        if node.module:
            self.analyzer.imports[self.file_path].add(node.module)
            for alias in node.names:
                self.analyzer.imports[self.file_path].add(f"{node.module}.{alias.name}")
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        """Обработка определений классов"""
        class_name = node.name
        
        # Собираем информацию о классе
        class_info = {
            'file': self.file_path,
            'methods': [],
            'bases': [self._get_name(base) for base in node.bases],
            'decorators': [self._get_decorator_name(dec) for dec in node.decorator_list],
            'is_abstract': False,
            'init_params': []
        }
        
        # Проверяем, является ли ABC
        if any('ABC' in base for base in class_info['bases']):
            class_info['is_abstract'] = True
            self.analyzer.interfaces[class_name] = class_info
        
        self.current_class = class_name
        
        # Анализируем методы класса
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_name = item.name
                class_info['methods'].append(method_name)
                
                # Особое внимание __init__
                if method_name == '__init__':
                    class_info['init_params'] = self._analyze_function_args(item)
        
        self.analyzer.classes[class_name] = class_info
        
        # Регистрируем декораторы
        for dec_name in class_info['decorators']:
            self.analyzer.decorators[dec_name].append(('class', class_name))
        
        self.generic_visit(node)
        self.current_class = None
    
    def visit_FunctionDef(self, node):
        """Обработка определений функций"""
        func_name = node.name
        
        # Если это метод класса, уже обработан в visit_ClassDef
        if self.current_class:
            self.generic_visit(node)
            return
        
        # Это функция верхнего уровня
        func_info = {
            'file': self.file_path,
            'args': self._analyze_function_args(node),
            'decorators': [self._get_decorator_name(dec) for dec in node.decorator_list],
            'calls': []
        }
        
        self.analyzer.functions[func_name] = func_info
        
        # Регистрируем декораторы
        for dec_name in func_info['decorators']:
            self.analyzer.decorators[dec_name].append(('function', func_name))
        
        self.generic_visit(node)
    
    def _get_name(self, node):
        """Извлечение имени из AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        else:
            return str(node)
    
    def _get_decorator_name(self, node):
        """Извлечение имени декоратора"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        else:
            return str(node)
    
    def _analyze_function_args(self, node):
        """Анализ аргументов функции"""
        args_info = []
        
        # Позиционные аргументы
        for arg in node.args.args:
            arg_info = {
                'name': arg.arg,
                'type_hint': self._get_name(arg.annotation) if arg.annotation else None,
                'optional': False
            }
            args_info.append(arg_info)
        
        # Аргументы со значениями по умолчанию
        defaults_count = len(node.args.defaults)
        if defaults_count > 0:
            # Помечаем последние N аргументов как optional
            for i in range(len(args_info) - defaults_count, len(args_info)):
                if i >= 0:
                    args_info[i]['optional'] = True
        
        return args_info


def main():
    """Основная функция анализа"""
    if len(sys.argv) < 2:
        print("Usage: python architecture_scanner.py <project_root>")
        sys.exit(1)
    
    project_root = sys.argv[1]
    
    analyzer = ArchitecturalAnalyzer(project_root)
    analyzer.analyze()
    
    report = analyzer.generate_report()
    
    # Сохраняем отчет
    output_file = Path(project_root) / "plans" / "architecture_gap_analysis" / "ast_analysis_report.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"📊 Отчет сохранен в {output_file}")
    
    # Краткая сводка в консоль
    print("\n🎯 КРАТКАЯ СВОДКА:")
    print(f"   Классов: {report['summary']['total_classes']}")
    print(f"   Функций: {report['summary']['total_functions']}")
    print(f"   Модулей: {report['summary']['total_modules']}")
    print(f"   Синглтонов: {report['summary']['singletons']}")
    print(f"   Фабрик: {report['summary']['factories']}")
    print(f"   DI паттернов: {report['summary']['di_patterns']}")
    
    print("\n🏆 ТОП КАНДИДАТОВ НА ORCHESTRATOR:")
    for i, candidate in enumerate(report['orchestrator_candidates'][:3], 1):
        print(f"   {i}. {candidate['class']} (score: {candidate['score']})")
        print(f"      📁 {candidate['file']}")
        print(f"      🔹 {', '.join(candidate['reasons'])}")
    
    print("\n❌ ОТСУТСТВУЮЩИЕ КОМПОНЕНТЫ:")
    for missing in report['missing_components']['classes'][:5]:
        print(f"   - {missing}")


if __name__ == "__main__":
    main() 