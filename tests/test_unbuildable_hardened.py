import pytest
from security.ast_attack_detector import ASTAttackDetector, AttackPattern
from security.native_seccomp_filter import NativeSeccompFilter, SeccompProfile
from security.hsm_pqc_signer import HSM_PQC_Signer, HSMConfig

def test_ast_attack_detector():
    detector = ASTAttackDetector()

    # Test safe code
    safe_code = "x = 1 + 1"
    is_safe, violations = detector.validate_transformation(safe_code)
    assert is_safe
    assert len(violations) == 0

    # Test code injection (eval)
    unsafe_code = "eval('1 + 1')"
    is_safe, violations = detector.validate_transformation(unsafe_code)
    assert not is_safe
    assert any(v.pattern == AttackPattern.CODE_INJECTION for v in violations)

    # Test process spawn
    unsafe_code2 = "import subprocess\nsubprocess.run(['ls', '-la'])"
    is_safe, violations = detector.validate_transformation(unsafe_code2)
    assert not is_safe
    assert any(v.pattern == AttackPattern.PROCESS_SPAWN for v in violations)

def test_hsm_pqc_signer_mock():
    # Since we don't have a real HSM in test, we can only verify it fails initialization
    # cleanly or mocking it if necessary.
    config = HSMConfig(pkcs11_library="/tmp/non_existent.so")
    signer = HSM_PQC_Signer(config)

    # Should fail cleanly
    result = signer.sign_transformation("x = 1")
    assert result["status"] == "error"

def test_seccomp_wrapper():
    # Native filter testing
    filter = NativeSeccompFilter(lib_path="/tmp/non_existent.so")
    assert not filter.apply(SeccompProfile.MODERATE)
