#!/usr/bin/env python3
"""Fast structural checks for the consolidated substrate test module."""
import ast
from collections import Counter
from pathlib import Path
import sys

path = Path('test_substrates.py')
tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
tests = [node.name for node in tree.body if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')]
duplicates = sorted(name for name, count in Counter(tests).items() if count > 1)
missing_timeouts = [node.lineno for node in ast.walk(tree) if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == 'subprocess' and node.func.attr == 'run'
                    and not any(keyword.arg == 'timeout' for keyword in node.keywords)]
pytest_mains = [node.lineno for node in ast.walk(tree) if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
                and node.func.value.id == 'pytest' and node.func.attr == 'main']
bare_excepts = [node.lineno for node in ast.walk(tree) if isinstance(node, ast.ExceptHandler) and node.type is None]
problems = []
if duplicates: problems.append('duplicate test functions: {}'.format(', '.join(duplicates)))
if missing_timeouts: problems.append('subprocess.run without timeout at lines: {}'.format(missing_timeouts))
if pytest_mains: problems.append('pytest.main in test module at lines: {}'.format(pytest_mains))
if bare_excepts: problems.append('bare except at lines: {}'.format(bare_excepts))
if problems:
    print('\n'.join('ERROR: ' + problem for problem in problems), file=sys.stderr)
    raise SystemExit(1)
print('test-suite structural checks passed')
