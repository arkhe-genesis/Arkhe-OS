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
            # Reconstruct HumanityProof properly from dict, making sure not to mutate in place
            # as it might cause issues on subsequent reads if fetched from memory cache
            proof_data = cached_proof.copy()

            # Defensive conversion just in case it is read from strings
            if isinstance(proof_data.get("status"), str):
                proof_data["status"] = VerificationStatus(proof_data["status"])

            new_stamps = []
            for s in proof_data.get("stamps", []):
                if isinstance(s, dict):
                    new_stamps.append(StampCredential(**s))
                else:
                    new_stamps.append(s)
            proof_data["stamps"] = new_stamps

            return HumanityProof(**proof_data)
"""

content = re.sub(r'    async def is_human\(.*?return HumanityProof\(\*\*proof_data\)\n', replacement.lstrip(), content, flags=re.DOTALL)

with open("node/passport_gateway.py", "w") as f:
    f.write(content)
