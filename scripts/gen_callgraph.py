#!/usr/bin/env python3
"""Generate callgraph and AST hashes for sboxmgr source code."""

import ast
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class CallGraphVisitor(ast.NodeVisitor):
    """AST visitor to extract function calls and definitions."""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.module_name = self._get_module_name(filename)
        self.current_class = None
        self.current_function = None
        self.calls: List[Tuple[str, str, str]] = []  # (caller, callee, line)
        self.definitions: List[Tuple[str, str, str]] = []  # (name, type, line)
        
    def _get_module_name(self, filename: str) -> str:
        """Extract module name from filename."""
        rel_path = os.path.relpath(filename, "src")
        return rel_path.replace("/", ".").replace(".py", "")
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition."""
        old_class = self.current_class
        self.current_class = node.name
        self.definitions.append((node.name, "class", str(node.lineno)))
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition."""
        old_function = self.current_function
        self.current_function = node.name
        
        # Create full name
        if self.current_class:
            full_name = f"{self.current_class}.{node.name}"
        else:
            full_name = node.name
            
        self.definitions.append((full_name, "function", str(node.lineno)))
        self.generic_visit(node)
        self.current_function = old_function
    
    def visit_Call(self, node: ast.Call):
        """Visit function call."""
        if isinstance(node.func, ast.Name):
            callee = node.func.id
        elif isinstance(node.func, ast.Attribute):
            callee = node.func.attr
        else:
            callee = "unknown"
            
        # Create caller name
        if self.current_class and self.current_function:
            caller = f"{self.current_class}.{self.current_function}"
        elif self.current_function:
            caller = self.current_function
        else:
            caller = "module"
            
        self.calls.append((caller, callee, str(node.lineno)))
        self.generic_visit(node)


def get_ast_hash(content: str) -> str:
    """Generate hash from AST."""
    tree = ast.parse(content)
    # Convert AST to string representation for hashing
    ast_str = ast.dump(tree, include_attributes=False)
    return hashlib.sha256(ast_str.encode()).hexdigest()[:16]


def analyze_file(filename: str) -> Dict:
    """Analyze a single Python file."""
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        visitor = CallGraphVisitor(filename)
        visitor.visit(ast.parse(content))
        
        return {
            "filename": filename,
            "module": visitor.module_name,
            "ast_hash": get_ast_hash(content),
            "definitions": visitor.definitions,
            "calls": visitor.calls,
            "lines": len(content.splitlines())
        }
    except Exception as e:
        return {
            "filename": filename,
            "error": str(e),
            "ast_hash": None,
            "definitions": [],
            "calls": [],
            "lines": 0
        }


def find_python_files(src_dir: str) -> List[str]:
    """Find all Python files in src directory."""
    files = []
    for root, dirs, filenames in os.walk(src_dir):
        # Skip __pycache__ and .git
        dirs[:] = [d for d in dirs if d not in ('__pycache__', '.git')]
        for filename in filenames:
            if filename.endswith('.py'):
                files.append(os.path.join(root, filename))
    return sorted(files)


def generate_callgraph(src_dir: str = "src/sboxmgr") -> Dict:
    """Generate callgraph and AST analysis."""
    files = find_python_files(src_dir)
    
    print(f"Analyzing {len(files)} Python files...")
    
    results = []
    all_calls = []
    all_definitions = []
    
    for filename in files:
        result = analyze_file(filename)
        results.append(result)
        all_calls.extend(result.get("calls", []))
        all_definitions.extend(result.get("definitions", []))
        
        if "error" in result:
            print(f"⚠️  Error in {filename}: {result['error']}")
        else:
            print(f"✅ {filename} ({result['lines']} lines, {len(result['calls'])} calls)")
    
    # Create callgraph
    callgraph = {}
    for caller, callee, line in all_calls:
        if caller not in callgraph:
            callgraph[caller] = []
        callgraph[caller].append({"callee": callee, "line": line})
    
    return {
        "metadata": {
            "total_files": len(files),
            "total_calls": len(all_calls),
            "total_definitions": len(all_definitions),
            "generated_at": str(Path().absolute())
        },
        "files": results,
        "callgraph": callgraph,
        "statistics": {
            "files_by_module": {},
            "calls_by_module": {},
            "definitions_by_type": {}
        }
    }


def main():
    """Main function."""
    if len(sys.argv) > 1:
        src_dir = sys.argv[1]
    else:
        src_dir = "src/sboxmgr"
    
    print(f"🔍 Analyzing source code in: {src_dir}")
    
    result = generate_callgraph(src_dir)
    
    # Save results
    with open("callgraph_src.json", "w") as f:
        json.dump(result, f, indent=2)
    
    with open("ast_hashes.txt", "w") as f:
        for file_info in result["files"]:
            if "ast_hash" in file_info and file_info["ast_hash"]:
                f.write(f"{file_info['ast_hash']} {file_info['filename']}\n")
    
    # Generate DOT file for visualization
    with open("callgraph_src.dot", "w") as f:
        f.write("digraph CallGraph {\n")
        f.write("  rankdir=LR;\n")
        f.write("  node [shape=box];\n\n")
        
        for caller, calls in result["callgraph"].items():
            for call in calls:
                callee = call["callee"]
                f.write(f'  "{caller}" -> "{callee}";\n')
        
        f.write("}\n")
    
    print("\n📊 Results saved:")
    print("  📄 callgraph_src.json - Full analysis")
    print("  🔗 callgraph_src.dot - Graphviz DOT file")
    print("  🆔 ast_hashes.txt - AST hashes")
    
    print("\n📈 Statistics:")
    print(f"  📁 Files: {result['metadata']['total_files']}")
    print(f"  📞 Calls: {result['metadata']['total_calls']}")
    print(f"  📝 Definitions: {result['metadata']['total_definitions']}")


if __name__ == "__main__":
    main() 