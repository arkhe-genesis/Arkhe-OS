import re

with open("node/passport_gateway.py", "r") as f:
    content = f.read()

replacement = """
    async def is_human(
        self,
        address: str,
        min_score: Optional[float] = None,
        orcid_id: Optional[str] = None,
    ) -> HumanityProof:
        \"\"\"
        Verifica se endereço é humano via Passport + ORCID.
        Retorna HumanityProof com seal canônico e tenta cache distribuído.
        \"\"\"
        cached_proof = await self.cache.get(address, "humanity")
        if cached_proof:
            # Reconstruct HumanityProof properly from dict
            cached_proof["status"] = VerificationStatus(cached_proof["status"])
            cached_proof["stamps"] = [StampCredential(**s) for s in cached_proof.get("stamps", [])]
            return HumanityProof(**cached_proof)
"""

content = re.sub(r'    async def is_human\(.*?return HumanityProof\(\*\*cached_proof\)', replacement.lstrip(), content, flags=re.DOTALL)

with open("node/passport_gateway.py", "w") as f:
    f.write(content)
