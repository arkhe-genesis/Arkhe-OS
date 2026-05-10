import pytest
from substrate_157 import FerrisCompiler

def test_ferris_compiler_initialization():
    ferris = FerrisCompiler()
    assert ferris.metrics['modules_transpiled'] == 0
    assert ferris.metrics['lines_of_go_generated'] == 0
    assert ferris.metrics['compilation_time_ms'] == 0.0

def test_ferris_transpile():
    ferris = FerrisCompiler()
    python_code = "def say_hello():\n    print('Hello')"
    go_code = ferris.transpile(python_code, "hello_module")

    assert "package main" in go_code
    assert "hello_module" in go_code
    assert ferris.metrics['modules_transpiled'] == 1
    assert ferris.metrics['lines_of_go_generated'] > 0
    assert ferris.metrics['compilation_time_ms'] >= 0.0
