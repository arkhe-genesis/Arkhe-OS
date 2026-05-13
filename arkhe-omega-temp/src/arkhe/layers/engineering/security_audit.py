# src/arkhe/layers/engineering/security_audit.py
import hashlib

def audit_security(file_path: str) -> dict:
    with open(file_path, 'r') as f:
        content = f.read()
    issues = []
    if 'eval(' in content:
        issues.append("Use of eval() detected")
    if 'exec(' in content:
        issues.append("Use of exec() detected")
    if 'import sqlite3' in content and '?' in content:
        pass  # ok
    score = 10 - len(issues)
    return {"score": max(0, score), "issues": issues}
