import pytest
from arkhe_stdlib.audit_hooks import auditor

def test_audit_hook_logging():
    initial_count = auditor.blocked_calls
    seal = auditor.log_blocked_action(
        function_name="test_func",
        payload="test_payload",
        severity="high",
        reason="TEST_REASON"
    )
    assert auditor.blocked_calls == initial_count + 1
    assert isinstance(seal, str)
    assert len(seal) > 0
