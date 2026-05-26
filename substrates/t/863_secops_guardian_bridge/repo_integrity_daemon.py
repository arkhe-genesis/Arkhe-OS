#!/ "repo_integrity_daemon.py"
import requests
import hashlib
import time
import json

SUSPICIOUS_PATTERNS = [
    "security", "wallet", "auditor", "defi", "risk", "scanner",
    "checker", "validator", "protector", "guard", "shield"
]

class RepoIntegrityDaemon:
    def __init__(self, webhook_url=None):
        self.webhook_url = webhook_url
        self.known_bad = set()

    def scan_pypi(self):
        resp = requests.get("https://pypi.org/rss/packages.xml", timeout=10)
        # Requires XML parsing to extract package titles from resp.text
        # new_packages = parse_rss_titles(resp.text)
        new_packages = ["wallet-security-checker", "eth-security-auditor"] # TODO: Replace with actual parsed data
        for pkg in new_packages:
            if any(pattern in pkg.lower() for pattern in SUSPICIOUS_PATTERNS):
                self.flag_package(pkg, "PyPI")

    def flag_package(self, name, registry):
        seal_str = name + ":" + registry
        seal = hashlib.sha3_256(seal_str.encode()).hexdigest()[:16]
        alert = "[ALERTA] Pacote suspeito detectado: " + name + " (" + registry + "). Selo: " + seal
        print(alert)
        if self.webhook_url:
            requests.post(self.webhook_url, json={"alert": alert, "seal": seal})

if __name__ == "__main__":
    daemon = RepoIntegrityDaemon()
    daemon.scan_pypi()
