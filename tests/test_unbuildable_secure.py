import pytest
import os
import ast
from substrates.unbuildable_secure import RecursiveSubstrateSecure, ASTSecurityValidator

def test_ast_validation():
    # Valid AST
    code = "x = 1 + 1"
    valid, violations = ASTSecurityValidator.validate(code)
    assert valid
    assert not violations

    # Invalid AST (eval)
    code2 = "eval('1 + 1')"
    valid, violations = ASTSecurityValidator.validate(code2)
    assert not valid
    assert any("Chamada proibida: eval" in v for v in violations) or any("eval" in v.lower() for v in violations)

def test_unbuildable_secure_init_fails_without_hsm():
    with pytest.raises(RuntimeError, match="Falha CRÍTICA ao conectar ao HSM"):
        substrate = RecursiveSubstrateSecure()
