import re

with open("node/temporal_chain_anchor.py", "r") as f:
    content = f.read()

replacement = """    def verify_anchor(self, anchor_id: str) -> bool:
        \"\"\"Verifica integridade de uma ancora.\"\"\"
        if anchor_id not in self.anchors:
            return False
        anchor = self.anchors[anchor_id]
        # Recomputar anchor
        recomputed = HumanityAnchor(
            anchor_id=anchor.anchor_id,
            proof_hash=anchor.proof_hash,
            proof_seal=anchor.proof_seal,
            block_id=anchor.block_id,
            timestamp=anchor.timestamp,
        )
        recomputed.compute_anchor()
        if recomputed.temporal_anchor != anchor.temporal_anchor:
            return False
        if anchor.orcid_signature and self.verify_key:
            return self.verify_signature(recomputed.temporal_anchor, anchor.orcid_signature, self.verify_key.encode().hex())
        return True"""

content = re.sub(r'(?m)^def verify_anchor.*?return True', replacement, content, flags=re.DOTALL)

with open("node/temporal_chain_anchor.py", "w") as f:
    f.write(content)
