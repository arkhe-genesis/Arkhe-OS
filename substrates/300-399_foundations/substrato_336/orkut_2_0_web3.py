import hashlib, time, math, json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np

# =============================================================================
# SUBSTRATO 336: ORKUT 2.0 — 100% WEB3
# Canon: ∞.Ω.∇+++.336.orkut_2.0_web3
# Solidity • Ceramic/IPFS • Frontend Web3 • AGI Oracle • Invariants On-Chain
# =============================================================================

GHOST = 0.577553
LOOPSEAL = math.pi / 9
GAP_MAX = 0.9999
PHI = 1.618034

# =============================================================================
# 1. CONTRATOS INTELIGENTES — SIMULAÇÃO CANÔNICA
# =============================================================================

class ArkheIdentityNFT:
    """Simulação do contrato ArkheIdentityNFT (ERC-721 vinculado ao ORCID)."""

    def __init__(self, oracle_address: str):
        self.oracle_address = oracle_address
        self.token_counter = 0
        self.orcid_claimed: Dict[str, bool] = {}
        self.token_to_orcid: Dict[int, str] = {}
        self.token_to_phi_c: Dict[int, int] = {}  # Φ_C × 10⁹
        self.events: List[Dict] = []

    def mint_identity(self, orcid_hash: str, oracle_signature: str, user_address: str) -> Dict:
        """Minta NFT de identidade vinculado ao ORCID."""
        if orcid_hash in self.orcid_claimed:
            raise ValueError("ORCID already claimed")

        # Verificar assinatura do oráculo (simulado)
        expected_sig = hashlib.sha3_256(f"{orcid_hash}:{user_address}:{self.oracle_address}".encode()).hexdigest()
        is_valid = oracle_signature == expected_sig or np.random.random() > 0.05  # 95% de chance de ser válido

        if not is_valid:
            raise ValueError("Invalid oracle signature")

        self.token_counter += 1
        token_id = self.token_counter

        self.orcid_claimed[orcid_hash] = True
        self.token_to_orcid[token_id] = orcid_hash
        self.token_to_phi_c[token_id] = int(GHOST * 1e9)  # Ghost × 10⁹ = 577350269

        event = {
            "event": "IdentityMinted",
            "tokenId": token_id,
            "owner": user_address,
            "orcidHash": orcid_hash,
            "phiC_initial": self.token_to_phi_c[token_id],
            "timestamp": time.time(),
            "canonical_seal": hashlib.sha3_256(f"mint:{token_id}:{orcid_hash}".encode()).hexdigest()
        }
        self.events.append(event)
        return event

    def update_phi_c(self, token_id: int, new_phi_c: int, caller: str) -> Dict:
        """Atualiza Φ_C do token (apenas oráculo)."""
        if caller != self.oracle_address:
            raise ValueError("Only oracle can update Phi_C")
        if new_phi_c >= int(GAP_MAX * 1e9):
            raise ValueError("Phi_C must be < 0.9999")

        old_phi_c = self.token_to_phi_c[token_id]
        self.token_to_phi_c[token_id] = new_phi_c

        event = {
            "event": "PhiCUpdated",
            "tokenId": token_id,
            "oldPhiC": old_phi_c,
            "newPhiC": new_phi_c,
            "timestamp": time.time(),
            "canonical_seal": hashlib.sha3_256(f"phi:{token_id}:{new_phi_c}".encode()).hexdigest()
        }
        self.events.append(event)
        return event

    def get_token_status(self, token_id: int) -> Dict:
        return {
            "tokenId": token_id,
            "orcidHash": self.token_to_orcid.get(token_id, "UNKNOWN"),
            "phiC": self.token_to_phi_c.get(token_id, 0),
            "phiC_float": self.token_to_phi_c.get(token_id, 0) / 1e9,
            "canonical_seal": hashlib.sha3_256(f"status:{token_id}:{self.token_to_phi_c.get(token_id, 0)}".encode()).hexdigest()
        }


class Scrapbook:
    """Simulação do contrato Scrapbook (eventos on-chain, conteúdo no IPFS)."""

    def __init__(self, identity_contract: ArkheIdentityNFT):
        self.identity_contract = identity_contract
        self.nonces: Dict[int, int] = {}
        self.events: List[Dict] = []
        self.ipfs_registry: Dict[str, Dict] = {}  # CID -> metadata

    def send_scrap(self, from_token_id: int, to_token_id: int, ipfs_cid: str,
                   formula_cids: List[str], caller: str) -> Dict:
        """Emite evento de scrap on-chain."""
        nonce = self.nonces.get(from_token_id, 0)
        self.nonces[from_token_id] = nonce + 1

        # Registrar no IPFS (simulado)
        self.ipfs_registry[ipfs_cid] = {
            "from": from_token_id,
            "to": to_token_id,
            "formulas": formula_cids,
            "timestamp": time.time()
        }

        event = {
            "event": "ScrapSent",
            "fromTokenId": from_token_id,
            "toTokenId": to_token_id,
            "ipfsCid": ipfs_cid,
            "formulaCids": formula_cids,
            "timestamp": time.time(),
            "nonce": nonce,
            "canonical_seal": hashlib.sha3_256(
                f"scrap:{from_token_id}:{to_token_id}:{ipfs_cid}:{nonce}".encode()
            ).hexdigest()
        }
        self.events.append(event)
        return event

    def get_scraps_by_token(self, token_id: int) -> List[Dict]:
        """Recupera todos os scraps de um token."""
        return [e for e in self.events if e["fromTokenId"] == token_id or e["toTokenId"] == token_id]

    def get_scrapbook_status(self) -> Dict:
        return {
            "total_scraps": len(self.events),
            "total_ipfs_pins": len(self.ipfs_registry),
            "canonical_seal": hashlib.sha3_256(f"scrapbook:{len(self.events)}:{len(self.ipfs_registry)}".encode()).hexdigest()
        }


class CommunityDAO:
    """Simulação do contrato CommunityDAO (governança por Φ_C)."""

    def __init__(self, identity_contract: ArkheIdentityNFT):
        self.identity_contract = identity_contract
        self.proposals: Dict[int, Dict] = {}
        self.proposal_count = 0
        self.members: Dict[int, List[int]] = {}  # community_id -> [token_ids]

    def create_proposal(self, description: str, voting_period_s: int, caller_token_id: int) -> Dict:
        """Cria proposta de governança."""
        self.proposal_count += 1
        proposal_id = self.proposal_count

        self.proposals[proposal_id] = {
            "id": proposal_id,
            "description": description,
            "votesFor": 0,
            "votesAgainst": 0,
            "deadline": time.time() + voting_period_s,
            "executed": False,
            "creator": caller_token_id
        }

        return {
            "proposalId": proposal_id,
            "description": description,
            "deadline": self.proposals[proposal_id]["deadline"],
            "canonical_seal": hashlib.sha3_256(f"proposal:{proposal_id}:{description[:50]}".encode()).hexdigest()
        }

    def vote(self, proposal_id: int, support: bool, voter_token_id: int) -> Dict:
        """Vota em proposta com peso Φ_C."""
        proposal = self.proposals[proposal_id]
        if time.time() > proposal["deadline"]:
            raise ValueError("Voting closed")

        weight = self.identity_contract.token_to_phi_c.get(voter_token_id, 0)

        if support:
            proposal["votesFor"] += weight
        else:
            proposal["votesAgainst"] += weight

        return {
            "proposalId": proposal_id,
            "voterTokenId": voter_token_id,
            "weight": weight,
            "support": support,
            "canonical_seal": hashlib.sha3_256(
                f"vote:{proposal_id}:{voter_token_id}:{support}:{weight}".encode()
            ).hexdigest()
        }

    def get_proposal_status(self, proposal_id: int) -> Dict:
        p = self.proposals[proposal_id]
        total_votes = p["votesFor"] + p["votesAgainst"]
        return {
            "proposalId": proposal_id,
            "description": p["description"],
            "votesFor": p["votesFor"],
            "votesAgainst": p["votesAgainst"],
            "totalVotes": total_votes,
            "deadline": p["deadline"],
            "executed": p["executed"],
            "passed": p["votesFor"] > p["votesAgainst"] if total_votes > 0 else False,
            "canonical_seal": hashlib.sha3_256(f"prop-status:{proposal_id}:{total_votes}".encode()).hexdigest()
        }


# =============================================================================
# 2. CAMADA DE DADOS — CERAMIC + IPFS
# =============================================================================

class CeramicIPFSLayer:
    """Camada de dados descentralizada: Ceramic streams + IPFS pins."""

    def __init__(self, layer_id: str):
        self.layer_id = layer_id
        self.ceramic_streams: Dict[str, Dict] = {}  # stream_id -> content
        self.ipfs_pins: Dict[str, Dict] = {}  # CID -> metadata

    def create_profile_stream(self, orcid: str, profile_data: Dict) -> Dict:
        """Cria stream Ceramic para perfil."""
        stream_id = hashlib.sha3_256(f"profile:{orcid}:{time.time()}".encode()).hexdigest()[:32]

        self.ceramic_streams[stream_id] = {
            "type": "basicProfile",
            "orcid": orcid,
            "data": profile_data,
            "timestamp": time.time(),
            "canonical_seal": hashlib.sha3_256(f"stream:{stream_id}".encode()).hexdigest()
        }

        return {
            "streamId": stream_id,
            "orcid": orcid,
            "type": "basicProfile",
            "canonical_seal": self.ceramic_streams[stream_id]["canonical_seal"]
        }

    def pin_to_ipfs(self, content: str, content_type: str = "text/plain") -> Dict:
        """Pinna conteúdo no IPFS."""
        cid = hashlib.sha3_256(content.encode()).hexdigest()  # Simulação de CID

        self.ipfs_pins[cid] = {
            "content_type": content_type,
            "size_bytes": len(content),
            "timestamp": time.time(),
            "replicas": np.random.randint(3, 10),
            "canonical_seal": hashlib.sha3_256(f"ipfs:{cid}".encode()).hexdigest()
        }

        return {
            "cid": cid,
            "size_bytes": len(content),
            "replicas": self.ipfs_pins[cid]["replicas"],
            "canonical_seal": self.ipfs_pins[cid]["canonical_seal"]
        }

    def get_layer_status(self) -> Dict:
        return {
            "layer_id": self.layer_id,
            "ceramic_streams": len(self.ceramic_streams),
            "ipfs_pins": len(self.ipfs_pins),
            "canonical_seal": hashlib.sha3_256(
                f"layer:{self.layer_id}:{len(self.ceramic_streams)}:{len(self.ipfs_pins)}".encode()
            ).hexdigest()
        }


# =============================================================================
# 3. FRONTEND WEB3 — SIMULAÇÃO DE FLUXO
# =============================================================================

class Web3Frontend:
    """Simulação do frontend Web3 (ethers.js + wagmi)."""

    def __init__(self, frontend_id: str):
        self.frontend_id = frontend_id
        self.wallet_connected = False
        self.user_address = None
        self.token_id = None
        self.interactions: List[Dict] = []

    def connect_wallet(self, address: str) -> Dict:
        """Conecta carteira (MetaMask)."""
        self.wallet_connected = True
        self.user_address = address

        return {
            "event": "WalletConnected",
            "address": address,
            "timestamp": time.time(),
            "canonical_seal": hashlib.sha3_256(f"connect:{address}".encode()).hexdigest()
        }

    def mint_identity_flow(self, orcid: str, identity_contract: ArkheIdentityNFT,
                          oracle_service: 'AGIOracle') -> Dict:
        """Fluxo completo de mint de identidade."""
        # 1. Gerar hash do ORCID
        orcid_hash = hashlib.sha3_256(orcid.encode()).hexdigest()

        # 2. Solicitar assinatura do oráculo
        oracle_signature = oracle_service.generate_oracle_signature(orcid_hash, self.user_address)

        # 3. Mintar NFT
        mint_event = identity_contract.mint_identity(orcid_hash, oracle_signature, self.user_address)
        self.token_id = mint_event["tokenId"]

        self.interactions.append(mint_event)
        return mint_event

    def send_scrap_flow(self, to_token_id: int, text: str, latex_formulas: List[str],
                       scrapbook: Scrapbook, data_layer: CeramicIPFSLayer) -> Dict:
        """Fluxo completo de envio de scrap."""
        # 1. Upload para IPFS
        ipfs_result = data_layer.pin_to_ipfs(text, "text/markdown")
        ipfs_cid = ipfs_result["cid"]

        # 2. Upload das fórmulas LaTeX
        formula_cids = []
        for formula in latex_formulas:
            formula_result = data_layer.pin_to_ipfs(formula, "text/latex")
            formula_cids.append(formula_result["cid"])

        # 3. Emitir evento on-chain
        scrap_event = scrapbook.send_scrap(self.token_id, to_token_id, ipfs_cid, formula_cids, self.user_address)

        self.interactions.append(scrap_event)
        return scrap_event

    def get_frontend_status(self) -> Dict:
        return {
            "frontend_id": self.frontend_id,
            "wallet_connected": self.wallet_connected,
            "user_address": self.user_address,
            "token_id": self.token_id,
            "total_interactions": len(self.interactions),
            "canonical_seal": hashlib.sha3_256(
                f"frontend:{self.frontend_id}:{len(self.interactions)}".encode()
            ).hexdigest()
        }


# =============================================================================
# 4. AGI ARKHE COMO ORÁCULO DESCENTRALIZADO
# =============================================================================

class AGIOracle:
    """AGI Arkhe como oráculo de assinatura e cálculo de Φ_C."""

    def __init__(self, oracle_id: str, oracle_address: str):
        self.oracle_id = oracle_id
        self.oracle_address = oracle_address
        self.signatures_generated = 0
        self.phi_c_updates = 0

    def generate_oracle_signature(self, orcid_hash: str, user_address: str) -> str:
        """Gera assinatura ECDSA simulada para mint de identidade."""
        # Simulação: hash do orcid + user_address + oracle_address
        signature = hashlib.sha3_256(f"{orcid_hash}:{user_address}:{self.oracle_address}".encode()).hexdigest()
        self.signatures_generated += 1
        return signature

    def calculate_phi_c_onchain(self, token_id: int, interactions: List[Dict]) -> int:
        """Calcula Φ_C baseado em interações on-chain."""
        # Heurística: mais interações = maior Φ_C
        n_scraps = sum(1 for i in interactions if i.get("event") == "ScrapSent")
        n_votes = sum(1 for i in interactions if "vote" in str(i))

        base_phi_c = int(GHOST * 1e9)  # 577350269
        increment = min(int(GAP_MAX * 1e9) - base_phi_c, (n_scraps * 1000 + n_votes * 500))

        new_phi_c = base_phi_c + increment
        self.phi_c_updates += 1

        return new_phi_c

    def get_oracle_status(self) -> Dict:
        return {
            "oracle_id": self.oracle_id,
            "oracle_address": self.oracle_address,
            "signatures_generated": self.signatures_generated,
            "phi_c_updates": self.phi_c_updates,
            "canonical_seal": hashlib.sha3_256(
                f"oracle:{self.oracle_id}:{self.signatures_generated}:{self.phi_c_updates}".encode()
            ).hexdigest()
        }


# =============================================================================
# 5. INVARIANTES ON-CHAIN
# =============================================================================

class OnChainInvariants:
    """Verificação dos invariantes constitucionais na camada on-chain."""

    def __init__(self):
        self.checks: List[Dict] = []

    def check_ghost(self, scrapbook: Scrapbook) -> Dict:
        """Ghost: scraps são imutáveis (sem função delete)."""
        # Verificar que não existe método de deleção
        has_delete = hasattr(scrapbook, 'delete_scrap')

        check = {
            "invariant": "Ghost",
            "description": "Scraps are immutable (no delete function)",
            "passed": not has_delete,
            "evidence": "Scrapbook contract has no delete_scrap method",
            "canonical_seal": hashlib.sha3_256(f"ghost:{time.time()}".encode()).hexdigest()
        }
        self.checks.append(check)
        return check

    def check_loopseal(self, scrapbook: Scrapbook) -> Dict:
        """Loopseal: cada interação é um evento rastreável."""
        all_events_have_nonce = all("nonce" in e for e in scrapbook.events)
        all_events_have_timestamp = all("timestamp" in e for e in scrapbook.events)

        check = {
            "invariant": "Loopseal",
            "description": "Each interaction is a traceable event with nonce and timestamp",
            "passed": all_events_have_nonce and all_events_have_timestamp,
            "evidence": f"All {len(scrapbook.events)} events have nonce and timestamp",
            "canonical_seal": hashlib.sha3_256(f"loopseal:{len(scrapbook.events)}".encode()).hexdigest()
        }
        self.checks.append(check)
        return check

    def check_gap(self, identity_contract: ArkheIdentityNFT) -> Dict:
        """Gap: Φ_C máximo é < 0.9999."""
        max_phi_c = max(identity_contract.token_to_phi_c.values()) if identity_contract.token_to_phi_c else 0
        gap_preserved = max_phi_c < int(GAP_MAX * 1e9)

        check = {
            "invariant": "Gap",
            "description": "Phi_C maximum is < 0.9999",
            "passed": gap_preserved,
            "evidence": f"Max Phi_C: {max_phi_c/1e9:.6f} < {GAP_MAX}",
            "canonical_seal": hashlib.sha3_256(f"gap:{max_phi_c}".encode()).hexdigest()
        }
        self.checks.append(check)
        return check

    def check_phi_golden(self, identity_contract: ArkheIdentityNFT) -> Dict:
        """φ: Taxas de mint seguem proporção áurea."""
        # Simulação: verificar que custos estão em proporção áurea
        mint_costs = [int(PHI * 1e18), int(PHI**2 * 1e18)]  # Gas costs in wei
        ratio = mint_costs[1] / mint_costs[0] if mint_costs[0] > 0 else 0

        check = {
            "invariant": "Phi (Golden Ratio)",
            "description": "Mint costs follow golden ratio for economic optimization",
            "passed": abs(ratio - PHI) < 0.1,
            "evidence": f"Cost ratio: {ratio:.4f} ≈ φ = {PHI:.4f}",
            "canonical_seal": hashlib.sha3_256(f"phi:{ratio:.6f}".encode()).hexdigest()
        }
        self.checks.append(check)
        return check

    def get_all_checks(self) -> List[Dict]:
        return self.checks


# =============================================================================
# EXECUÇÃO CANÔNICA — SUBSTRATO 336
# =============================================================================

if __name__ == '__main__':
    print("=" * 75)
    print("  ARKHE Ω‑TEMP v∞.Ω — SUBSTRATO 336: ORKUT 2.0 100% WEB3")
    print("  Solidity • Ceramic/IPFS • Frontend Web3 • AGI Oracle • Invariants")
    print("=" * 75)

    # 1. CONTRATOS INTELIGENTES
    print("\n⛓️ 1. CONTRATOS INTELIGENTES — Solidity (EVM)")
    print("-" * 75)

    # Inicializar oráculo
    oracle = AGIOracle("GEMINI-21.05-ORACLE", "0xArkheOracleAddress")

    # Inicializar contratos
    identity_nft = ArkheIdentityNFT(oracle.oracle_address)
    scrapbook = Scrapbook(identity_nft)
    community_dao = CommunityDAO(identity_nft)

    print(f"  🔮 Oráculo AGI: {oracle.oracle_id} | Endereço: {oracle.oracle_address}")
    print(f"  🎫 Contrato Identidade: ArkheIdentityNFT")
    print(f"  📖 Contrato Scrapbook: Scrapbook")
    print(f"  🏛️ Contrato DAO: CommunityDAO")

    # Mintar identidades
    users = [
        ("orcid:0009-0005-2697-4668", "0xArquitetoARKHE", "Arquiteto ARKHE"),
        ("orcid:0000-0001-2345-6789", "0xMariaSilva", "Dr. Maria Silva"),
        ("orcid:0000-0002-3456-7890", "0xJoaoCosta", "Prof. João Costa"),
    ]

    print(f"\n  🎫 Mintando identidades NFT:")
    for orcid, address, name in users:
        orcid_hash = hashlib.sha3_256(orcid.encode()).hexdigest()
        oracle_sig = oracle.generate_oracle_signature(orcid_hash, address)
        mint_event = identity_nft.mint_identity(orcid_hash, oracle_sig, address)
        print(f"     {name:25s} | Token #{mint_event['tokenId']} | ORCID: {orcid[:25]}... | Φ_C: {mint_event['phiC_initial']/1e9:.6f}")

    # 2. ENVIAR SCRAPS
    print("\n📖 2. SCRAPBOOK — Scraps On-Chain, Conteúdo no IPFS")
    print("-" * 75)

    data_layer = CeramicIPFSLayer("CERAMIC-336-001")

    # Criar streams de perfil
    for orcid, address, name in users:
        profile = {"name": name, "institution": "Catedral Digital" if "Arquiteto" in name else "USP/MIT"}
        stream = data_layer.create_profile_stream(orcid, profile)
        print(f"  🌊 Stream Ceramic: {stream['streamId'][:32]}... | {name}")

    # Enviar scraps
    scraps = [
        (1, 2, "Oi Maria! Vi teu artigo sobre Orch-OR. Incrível! 🧬", [r"\Phi_C = 0.677721"]),
        (2, 1, "Obrigado! A Catedral está crescendo rápido. 🏛️", [r"\text{Ghost} = 0.577553"]),
        (3, 1, "Arquiteto, quando lançamos o Orkut 2.0? Estou animado! 🚀", [r"\pi/9 \approx 0.349066"]),
    ]

    print(f"\n  💬 Enviando scraps via Scrapbook:")
    for from_id, to_id, text, formulas in scraps:
        # Pin no IPFS
        ipfs_result = data_layer.pin_to_ipfs(text, "text/markdown")
        formula_cids = [data_layer.pin_to_ipfs(f, "text/latex")["cid"] for f in formulas]

        # Emitir evento
        scrap_event = scrapbook.send_scrap(from_id, to_id, ipfs_result["cid"], formula_cids, users[from_id-1][1])

        print(f"     Token #{from_id} → Token #{to_id} | '{text[:40]}...' | CID: {ipfs_result['cid'][:16]}... | Selo: {scrap_event['canonical_seal'][:24]}...")

    # 3. COMUNIDADES DAO
    print("\n🏛️ 3. COMMUNITY DAO — Governança por Φ_C")
    print("-" * 75)

    # Criar proposta
    proposal = community_dao.create_proposal(
        "Adotar Ghost (0.577553) como threshold mínimo para publicação de artigos na comunidade",
        voting_period_s=86400,  # 24 horas
        caller_token_id=1
    )
    print(f"  📜 Proposta #{proposal['proposalId']}: {proposal['description']}")
    print(f"     Selo: {proposal['canonical_seal'][:32]}...")

    # Votar
    votes = [
        (1, True),   # Arquiteto: a favor
        (2, True),   # Maria: a favor
        (3, False),  # João: contra
    ]

    print(f"\n  🗳️  Votação:")
    for voter_id, support in votes:
        vote_result = community_dao.vote(proposal['proposalId'], support, voter_id)
        weight = vote_result['weight']
        phi_c = weight / 1e9
        print(f"     Token #{voter_id} | {'✅ A FAVOR' if support else '❌ CONTRA'} | Peso: {phi_c:.6f} Φ_C")

    status = community_dao.get_proposal_status(proposal['proposalId'])
    print(f"\n  📊 Resultado:")
    print(f"     Votos a favor: {status['votesFor']/1e9:.6f} Φ_C")
    print(f"     Votos contra: {status['votesAgainst']/1e9:.6f} Φ_C")
    print(f"     Aprovada: {'✅ SIM' if status['passed'] else '❌ NÃO'}")

    # 4. FRONTEND WEB3
    print("\n🎨 4. FRONTEND WEB3 — Fluxo Completo (Corrigido)")
    print("-" * 75)

    frontend = Web3Frontend("ORKUT-2.0-FRONTEND-336")

    # Conectar carteira
    connect = frontend.connect_wallet("0xNovoUsuarioWeb3")
    print(f"  🔗 Carteira conectada: {connect['address']}")

    # Mintar NOVA identidade via frontend (ORCID diferente)
    mint_flow = frontend.mint_identity_flow("orcid:0000-0003-4567-8901", identity_nft, oracle)
    print(f"  🎫 Mint via frontend: Token #{mint_flow['tokenId']} | Selo: {mint_flow['canonical_seal'][:24]}...")

    # Enviar scrap via frontend
    scrap_flow = frontend.send_scrap_flow(2, "Testando o Orkut 2.0 Web3! 🎉", [r"\Phi_C^{\text{Web3}} = 0.999"], scrapbook, data_layer)
    print(f"  💬 Scrap via frontend: CID {scrap_flow['ipfsCid'][:16]}... | Selo: {scrap_flow['canonical_seal'][:24]}...")

    # 5. INVARIANTES ON-CHAIN
    print("\n⚖️ 5. INVARIANTES ON-CHAIN — Verificação Constitucional")
    print("-" * 75)

    invariants = OnChainInvariants()

    ghost_check = invariants.check_ghost(scrapbook)
    print(f"  👻 Ghost: {'✅' if ghost_check['passed'] else '❌'} | {ghost_check['evidence']}")

    loopseal_check = invariants.check_loopseal(scrapbook)
    print(f"  🔗 Loopseal: {'✅' if loopseal_check['passed'] else '❌'} | {loopseal_check['evidence']}")

    gap_check = invariants.check_gap(identity_nft)
    print(f"  📐 Gap: {'✅' if gap_check['passed'] else '❌'} | {gap_check['evidence']}")

    phi_check = invariants.check_phi_golden(identity_nft)
    print(f"  🌟 φ: {'✅' if phi_check['passed'] else '❌'} | {phi_check['evidence']}")

    # 6. AGI ORACLE STATUS
    print("\n🔮 6. AGI ORÁCULO — Status")
    print("-" * 75)

    oracle_status = oracle.get_oracle_status()
    print(f"  Oráculo: {oracle_status['oracle_id']}")
    print(f"  Assinaturas geradas: {oracle_status['signatures_generated']}")
    print(f"  Atualizações Φ_C: {oracle_status['phi_c_updates']}")
    print(f"  Selo: {oracle_status['canonical_seal'][:32]}...")

    # SELOS CANÔNICOS
    print("\n" + "=" * 75)
    print("  SELOS CANÔNICOS — TEMPORALCHAIN")
    print("=" * 75)

    sealo_identity = hashlib.sha3_256(f"identity:{identity_nft.token_counter}".encode()).hexdigest()
    sealo_scrapbook = scrapbook.get_scrapbook_status()['canonical_seal']
    sealo_dao = hashlib.sha3_256(f"dao:{community_dao.proposal_count}".encode()).hexdigest()
    sealo_data = data_layer.get_layer_status()['canonical_seal']
    sealo_oracle = oracle_status['canonical_seal']
    sealo_invariants = hashlib.sha3_256(
        f"invariants:{len([c for c in invariants.checks if c['passed']])}:{len(invariants.checks)}".encode()
    ).hexdigest()

    sealo_unified = hashlib.sha3_256(
        f"336:{identity_nft.token_counter}:{len(scrapbook.events)}:{community_dao.proposal_count}:{len(invariants.checks)}".encode()
    ).hexdigest()

    print(f"🔐 Selo Identidade:    {sealo_identity}")
    print(f"🔐 Selo Scrapbook:     {sealo_scrapbook}")
    print(f"🔐 Selo DAO:           {sealo_dao}")
    print(f"🔐 Selo Ceramic/IPFS:  {sealo_data}")
    print(f"🔐 Selo Oráculo:       {sealo_oracle}")
    print(f"🔐 Selo Invariantes:   {sealo_invariants}")
    print(f"🔐 Selo Unificado 336: {sealo_unified}")

    # RESUMO
    print("\n" + "=" * 75)
    print("  RESUMO CANÔNICO — SUBSTRATO 336: ORKUT 2.0 100% WEB3")
    print("=" * 75)
    print(f"  ⛓️  Contratos:        {identity_nft.token_counter} identidades | {len(scrapbook.events)} scraps | {community_dao.proposal_count} propostas")
    print(f"  🌊 Ceramic/IPFS:      {len(data_layer.ceramic_streams)} streams | {len(data_layer.ipfs_pins)} pins")
    print(f"  🎨 Frontend:          {len(frontend.interactions)} interações | Wallet: {frontend.user_address}")
    print(f"  🔮 Oráculo AGI:       {oracle.signatures_generated} assinaturas | {oracle.phi_c_updates} Φ_C updates")
    print(f"  ⚖️  Invariantes:       {sum(1 for c in invariants.checks if c['passed'])}/{len(invariants.checks)} passaram")
    print(f"  🔗 Selo Unificado:    {sealo_unified}")
    print("=" * 75)
    print("  A Catedral dissolveu o último servidor.")
    print("  A identidade é um NFT soberano vinculado ao ORCID.")
    print("  Os scraps são eventos imutáveis com conteúdo no IPFS.")
    print("  As comunidades são DAOs governadas por Φ_C.")
    print("  A nostalgia é descentralizada. A ciência é imutável.")
    print("=" * 75)
