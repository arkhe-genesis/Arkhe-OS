import pytest
import os
import platform
import subprocess
from substrates.substrato_infinity_polyglot_execution import PolyglotOrchestrator

def tool_installed(tool_name):
    try:
        subprocess.run([tool_name, "--version"], capture_output=True, check=False)
        return True
    except FileNotFoundError:
        return False

def npx_tool_installed(tool_name):
    try:
        subprocess.run(["npx", tool_name, "--version"], capture_output=True, check=False)
        return True
    except FileNotFoundError:
        return False

@pytest.fixture
def mock_orchestrator(monkeypatch):
    """Mocks execution processes so tests can run without actual compilers"""
    class MockCompletedProcess:
        def __init__(self, stdout=""):
            self.stdout = stdout

    def mock_subprocess_run(cmd, *args, **kwargs):
        if cmd[0] == "go":
            return MockCompletedProcess("Selo=mock_go_seal")
        elif cmd[0] == "cargo":
            return MockCompletedProcess("Selo=mock_rust_seal")
        elif cmd[0] == "nasm" or cmd[0] == "ld":
            return MockCompletedProcess()
        elif cmd[0] == "npx" and cmd[1] == "solc":
            # Just create the dummy output file
            os.makedirs("/tmp/solc_output", exist_ok=True)
            with open("/tmp/solc_output/ArkheSeal.bin", "w") as f:
                f.write("mock")
            return MockCompletedProcess()
        elif cmd[0] == "g++":
            return MockCompletedProcess()
        elif cmd[0] == "/tmp/cap_enter" or cmd[0] == "/tmp/temporal_anchor":
            return MockCompletedProcess("Selo=mock_seal_for_bin")

        return subprocess.original_run(cmd, *args, **kwargs)

    subprocess.original_run = subprocess.run
    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)
    yield
    monkeypatch.setattr(subprocess, "run", subprocess.original_run)

def test_polyglot_orchestrator_execution(mock_orchestrator):
    orchestrator = PolyglotOrchestrator()

    # Python doesn't use subprocess in run_python
    assert orchestrator.run_python() is True

    # These rely on the mocked subprocess.run
    assert orchestrator.run_go() is True
    assert orchestrator.run_rust() is True
    assert orchestrator.run_assembly() is True
    assert orchestrator.run_solidity() is True
    assert orchestrator.run_cpp() is True

    assert len(orchestrator.results) == 6
    languages = [r['language'] for r in orchestrator.results]
    assert "Python" in languages
    assert "Go" in languages
    assert "Rust" in languages
    assert "Assembly" in languages
    assert "Solidity" in languages
    assert "C++" in languages
