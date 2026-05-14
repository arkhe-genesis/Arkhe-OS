import pytest
from arkhe_stdlib import ArkheSecurityError
from arkhe_stdlib import safe_eval

def test_safe_eval_blocked():
    with pytest.raises(ArkheSecurityError) as exc:
        safe_eval.eval('__import__("os").system("ls")')
    assert "DANGEROUS_BUILTIN" in str(exc.value)

def test_safe_eval_allowed():
    result = safe_eval.eval('1 + 1')
    assert result == 2

def test_safe_exec_blocked():
    with pytest.raises(ArkheSecurityError) as exc:
        safe_eval.exec('open("/etc/passwd").read()')
    assert "DANGEROUS_BUILTIN" in str(exc.value)

def test_safe_exec_allowed():
    local_vars = {}
    safe_eval.exec('a = 10', globals(), local_vars)
    assert local_vars['a'] == 10

def test_safe_compile_blocked():
    with pytest.raises(ArkheSecurityError) as exc:
        safe_eval.compile('__import__("sys").exit()', '<string>', 'exec')
    assert "DANGEROUS_BUILTIN" in str(exc.value)
