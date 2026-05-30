import re

with open("node/temporal_chain_anchor.py", "r") as f:
    content = f.read()

replacement = """
        if recomputed.temporal_anchor != anchor.temporal_anchor:
            return False

        # If signing is enabled, the signature MUST be present and valid
        if self.verify_key:
            if not anchor.orcid_signature:
                return False
            return self.verify_signature(recomputed.temporal_anchor, anchor.orcid_signature, self.verify_key.encode().hex())

        return True
"""
content = re.sub(r'        if recomputed.temporal_anchor != anchor.temporal_anchor:.*?        return True\n', replacement.lstrip(), content, flags=re.DOTALL)

with open("node/temporal_chain_anchor.py", "w") as f:
    f.write(content)
