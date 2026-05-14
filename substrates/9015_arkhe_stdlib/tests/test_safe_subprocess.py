import pytest
from arkhe_stdlib import ArkheSecurityError
from arkhe_stdlib import safe_subprocess
import subprocess

def test_safe_subprocess_run_blocked():
    with pytest.raises(ArkheSecurityError) as exc:
        safe_subprocess.run(["bash", "-i"])
    assert "SANDBOX_VIOLATION" in str(exc.value)

def test_safe_subprocess_run_string_blocked():
    with pytest.raises(ArkheSecurityError) as exc:
        safe_subprocess.run("nc -lvp 4444", shell=True)
    assert "SANDBOX_VIOLATION" in str(exc.value)

def test_safe_subprocess_run_allowed():
    res = safe_subprocess.run(["echo", "hello"], capture_output=True, text=True)
    assert "hello" in res.stdout

def test_safe_subprocess_popen_blocked():
    with pytest.raises(ArkheSecurityError) as exc:
        safe_subprocess.Popen(["rm", "-rf", "/"])
    assert "SANDBOX_VIOLATION" in str(exc.value)

def test_safe_subprocess_popen_allowed():
    proc = safe_subprocess.Popen(["echo", "world"], stdout=subprocess.PIPE)
    stdout, _ = proc.communicate()
    assert b"world" in stdout
