# src/arkhe/layers/engineering/accessibility.py
import re
import hashlib

def audit_a11y(html: str) -> dict:
    issues = []
    if '<img' in html and 'alt=' not in html:
        issues.append("Missing alt text for images")
    if '<button' in html and '</button>' not in html:
        issues.append("Button not closed properly")
    if 'role=' not in html:
        issues.append("Consider adding ARIA roles")
    score = max(0, 100 - len(issues)*10)
    return {
        "passed": score > 90,
        "score": score,
        "issues": issues,
        "seal": hashlib.sha3_256(str(issues).encode()).hexdigest()[:8]
    }
