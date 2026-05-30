import re

with open("node/passport_gateway.py", "r") as f:
    content = f.read()

replacement_imports = """
import aiohttp

# Integracoes
from temporal_chain_anchor import TemporalChainAnchor
from proof_of_clean_hands import ProofOfCleanHands
from distributed_cache import DistributedCache
"""
content = content.replace("import aiohttp\n", replacement_imports)

replacement_init = """
    def __init__(
        self,
        api_key: Optional[str] = None,
        scorer_id: Optional[str] = None,
        orcid_client_id: Optional[str] = None,
        orcid_client_secret: Optional[str] = None,
        session: Optional[aiohttp.ClientSession] = None,
        temporal_anchor: Optional[TemporalChainAnchor] = None,
        proof_of_clean_hands: Optional[ProofOfCleanHands] = None,
        distributed_cache: Optional[DistributedCache] = None,
    ):
        self.api_key = api_key or PASSPORT_API_KEY
        self.scorer_id = scorer_id or PASSPORT_SCORER_ID
        self.orcid_client_id = orcid_client_id or ORCID_CLIENT_ID
        self.orcid_client_secret = orcid_client_secret or ORCID_CLIENT_SECRET
        self._session = session
        self._owned_session = session is None

        self.temporal_anchor = temporal_anchor or TemporalChainAnchor()
        self.proof_of_clean_hands = proof_of_clean_hands or ProofOfCleanHands()
        self.cache = distributed_cache or DistributedCache()
"""
content = re.sub(r'    def __init__\(\s*self,\s*api_key: Optional\[str\] = None,.*self\._owned_session = session is None\n', replacement_init.lstrip(), content, flags=re.DOTALL)

replacement_is_human = """
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
            return HumanityProof(**cached_proof)

        threshold = min_score if min_score is not None else MIN_HUMANITY_SCORE
        raw_score = 0.0
        stamps: List[StampCredential] = []
        status = VerificationStatus.PENDING

        try:
            score_data = await self.get_passport_score(address)
            raw_score = float(score_data.get("score", 0))
            stamps = await self.get_passport_stamps(address)
            status = VerificationStatus.VERIFIED
        except PassportGatewayError as e:
            status = VerificationStatus.ERROR
            # Em modo degradado, confiar em ORCID se disponível
            if orcid_id:
                status = VerificationStatus.PENDING

        normalized = min(raw_score / MIN_PASSPORT_SCORE, 1.0) if MIN_PASSPORT_SCORE > 0 else 0.0
        orcid_ok = await self.verify_orcid_link(address, orcid_id)

        # Proof of Clean Hands (AML)
        check = await self.proof_of_clean_hands.check_address(address)
        sanctions_clear = check.risk_level.value in ["clear", "low", "medium"]

        is_human = (normalized >= threshold) or orcid_ok

        proof = HumanityProof(
            address=address,
            is_human=is_human,
            score=normalized,
            raw_passport_score=raw_score,
            stamps=stamps,
            orcid_verified=orcid_ok,
            orcid_id=orcid_id,
            sanctions_clear=sanctions_clear,
            status=status,
        )
        proof.compute_seal()

        anchor = self.temporal_anchor.anchor_humanity_proof(proof.to_dict())
        proof.temporal_anchor = anchor.temporal_anchor

        await self.cache.set(address, proof.to_dict(), "humanity")
        return proof
"""
content = re.sub(r'    async def is_human\(\s*self,\s*address: str,.*return proof\n', replacement_is_human.lstrip(), content, flags=re.DOTALL)

with open("node/passport_gateway.py", "w") as f:
    f.write(content)
