import re

# File 1: repo_integrity_daemon.py
with open("substrates/t/863_secops_guardian_bridge/repo_integrity_daemon.py", "r") as f:
    content = f.read()

bad = """    def scan_pypi(self):
        resp = requests.get("https://pypi.org/rss/packages.xml", timeout=10)
        new_packages = ["wallet-security-checker", "eth-security-auditor"]
        for pkg in new_packages:"""
good = """    def scan_pypi(self):
        resp = requests.get("https://pypi.org/rss/packages.xml", timeout=10)
        # Requires XML parsing to extract package titles from resp.text
        # new_packages = parse_rss_titles(resp.text)
        new_packages = ["wallet-security-checker", "eth-security-auditor"] # TODO: Replace with actual parsed data
        for pkg in new_packages:"""

if bad in content:
    content = content.replace(bad, good)
    with open("substrates/t/863_secops_guardian_bridge/repo_integrity_daemon.py", "w") as f:
        f.write(content)
else:
    print("Failed to replace in repo_integrity_daemon.py")


# File 2: blockchain_z_glm.py
with open("substrates/t/870_blockchain_z_glm/blockchain_z_glm.py", "r") as f:
    content2 = f.read()

bad2 = """    def vote(self, validator_idx: int, proposal_id: int, support: bool):
        if proposal_id >= len(self.proposal_pool):
            return
        proposal = self.proposal_pool[proposal_id]"""

good2 = """    def vote(self, validator_idx: int, proposal_id: int, support: bool):
        if proposal_id >= len(self.proposal_pool):
            return
        if validator_idx in self.votes.setdefault(proposal_id, set()):
            return
        self.votes[proposal_id].add(validator_idx)
        proposal = self.proposal_pool[proposal_id]"""

if bad2 in content2:
    content2 = content2.replace(bad2, good2)
    with open("substrates/t/870_blockchain_z_glm/blockchain_z_glm.py", "w") as f:
        f.write(content2)
else:
    print("Failed to replace in blockchain_z_glm.py")
