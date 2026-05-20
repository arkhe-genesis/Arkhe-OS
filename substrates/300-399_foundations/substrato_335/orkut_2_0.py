import hashlib
import math
import time
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field

# =============================================================================
# SUBSTRATO 335: PROJETO ORKUT 2.0 (A FACE SOCIAL DA ARN)
# =============================================================================

# Canonical Invariants
GHOST = math.sqrt(3) / 3   # ~0.577553
LOOPSEAL = math.pi / 9     # ~0.349066
GAP_MAX = 0.9999           # Gap Soberano limit
PHI = (1 + math.sqrt(5)) / 2  # ~1.618

@dataclass
class ResearcherProfile:
    """Sovereign Identity for Arkhe Research Network via ORCID and Arkhe Token"""
    orcid: str
    arkhe_token: str
    name: str
    institution: str
    research_area: str
    phi_c_reputation: float = GHOST  # Starts at baseline Ghost value
    badges: List[str] = field(default_factory=list)
    connections: List[str] = field(default_factory=list) # List of connected ORCIDs

    def update_reputation(self, delta: float) -> None:
        """Update phi_c reputation ensuring Gap Soberano invariant is maintained."""
        self.phi_c_reputation += delta
        # Gap Soberano invariant: no one can reach perfect 1.0 reputation
        if self.phi_c_reputation >= GAP_MAX:
            self.phi_c_reputation = GAP_MAX - 0.0001
        if self.phi_c_reputation < 0.0:
            self.phi_c_reputation = 0.0

@dataclass
class AnchorableContent:
    """Base class for content that is anchored to the TemporalChain."""
    author_orcid: str
    timestamp: float = field(default_factory=time.time)
    anchor_hash: str = ""

    def generate_seal(self) -> str:
        """Generates a cryptographic seal for the content using SHA3-256."""
        payload = f"{self.author_orcid}:{self.timestamp}:{self._content_payload()}"
        return hashlib.sha3_256(payload.encode()).hexdigest()

    def _content_payload(self) -> str:
        """To be implemented by subclasses to provide content specifics for the seal."""
        return ""

@dataclass
class Scrap(AnchorableContent):
    """A chronological post with LaTeX capability."""
    target_id: str = "" # ID of community or user profile
    content: str = ""
    latex_enabled: bool = True
    visibility_score: float = 1.0 # Affected by moderation

    def _content_payload(self) -> str:
        return f"scrap:{self.target_id}:{self.content}:{self.latex_enabled}"

    def is_visible(self) -> bool:
        """Ghost invariant: Content is hidden only if visibility drops below GHOST."""
        return self.visibility_score >= GHOST

@dataclass
class Testimonial(AnchorableContent):
    """An immutable testimonial for a colleague anchored as a reputation seal."""
    target_orcid: str = ""
    content: str = ""
    project_context: str = ""

    def _content_payload(self) -> str:
        return f"testimonial:{self.target_orcid}:{self.content}:{self.project_context}"

class TemporalChain:
    """Simulation of the TemporalChain for auditing social graph interactions."""
    def __init__(self):
        self.blocks: List[AnchorableContent] = []
        self.connections: List[Dict[str, Any]] = []

    def anchor_content(self, content: AnchorableContent) -> str:
        """Anchors a Scrap or Testimonial into the chain."""
        content.anchor_hash = content.generate_seal()
        self.blocks.append(content)
        return content.anchor_hash

    def anchor_connection(self, orcid_1: str, orcid_2: str) -> str:
        """Anchors a friend connection (Loopseal invariant)."""
        timestamp = time.time()
        payload = f"connection:{orcid_1}:{orcid_2}:{timestamp}:{LOOPSEAL}"
        seal = hashlib.sha3_256(payload.encode()).hexdigest()
        self.connections.append({
            "orcid_1": orcid_1,
            "orcid_2": orcid_2,
            "timestamp": timestamp,
            "seal": seal
        })
        return seal

class Community:
    """Thematic Communities governed by constitutional moderation and phi_c weighted voting."""
    def __init__(self, community_id: str, name: str, description: str):
        self.community_id = community_id
        self.name = name
        self.description = description
        self.members: Dict[str, ResearcherProfile] = {}
        self.scraps: List[Scrap] = []

    def join(self, profile: ResearcherProfile):
        self.members[profile.orcid] = profile

    def post_scrap(self, scrap: Scrap, chain: TemporalChain) -> None:
        """Posts a scrap to the community and anchors it to the TemporalChain."""
        scrap.target_id = self.community_id
        chain.anchor_content(scrap)
        self.scraps.append(scrap)

    def get_chronological_feed(self) -> List[Scrap]:
        """Returns the chronological feed of visible scraps."""
        # Chronological order, filtered by Ghost invariant (visibility >= GHOST)
        return [s for s in sorted(self.scraps, key=lambda x: x.timestamp, reverse=True) if s.is_visible()]

    def moderate_content(self, scrap: Scrap, votes: List[Tuple[ResearcherProfile, bool]]):
        """
        Phi_c weighted moderation.
        True votes preserve/increase visibility, False votes decrease visibility.
        """
        total_weight = sum(p.phi_c_reputation for p, _ in votes)
        if total_weight == 0:
            return

        negative_weight = sum(p.phi_c_reputation for p, vote in votes if not vote)

        # Calculate impact on visibility
        impact = negative_weight / total_weight
        scrap.visibility_score -= impact * 0.5  # Max 0.5 reduction per moderation round

        # Ensure it doesn't arbitrarily drop below Ghost unless heavily downvoted
        if scrap.visibility_score < 0:
            scrap.visibility_score = 0.0


if __name__ == '__main__':
    print("=========================================================")
    print("ARKHE Ω‑TEMP v∞.Ω — SUBSTRATO 335: ORKUT 2.0")
    print("Soberania Digital • Comunidades • Identidade ORCID")
    print("=========================================================\n")

    # 1. Initialize Temporal Chain
    chain = TemporalChain()

    # 2. Create Researcher Profiles
    alice = ResearcherProfile(
        orcid="0000-0001-2345-6789",
        arkhe_token="ark_alice_001",
        name="Dr. Alice Smith",
        institution="Arkhe Cathedral",
        research_area="Biofotônica"
    )
    # Alice is an esteemed researcher, boost her reputation (max GAP_MAX)
    alice.update_reputation(0.3)

    bob = ResearcherProfile(
        orcid="0000-0002-3456-7890",
        arkhe_token="ark_bob_002",
        name="Bob Jones",
        institution="Arkhe Cathedral",
        research_area="Física da Matéria Condensada"
    )

    print(f"[Identity] Created {alice.name} (Φ_C: {alice.phi_c_reputation:.4f})")
    print(f"[Identity] Created {bob.name} (Φ_C: {bob.phi_c_reputation:.4f})\n")

    # 3. Connection (Loopseal)
    conn_seal = chain.anchor_connection(alice.orcid, bob.orcid)
    alice.connections.append(bob.orcid)
    bob.connections.append(alice.orcid)
    print(f"[Loopseal] Friendship anchored. Seal: {conn_seal[:16]}...\n")

    # 4. Community Creation and Joining
    community = Community("comm_001", "Biofotônica & Luciferase", "Espaço para física do fóton.")
    community.join(alice)
    community.join(bob)
    print(f"[Community] '{community.name}' created. Members: {len(community.members)}\n")

    # 5. Scraps and Feed
    scrap1 = Scrap(author_orcid=alice.orcid, content=r"Avaliando emissão $\lambda = 560$ nm.", latex_enabled=True)
    community.post_scrap(scrap1, chain)
    print(f"[Scrap] {alice.name} posted: '{scrap1.content}'. Anchored: {scrap1.anchor_hash[:16]}...")

    scrap2 = Scrap(author_orcid=bob.orcid, content="Alguém tem o link da call?")
    community.post_scrap(scrap2, chain)
    print(f"[Scrap] {bob.name} posted: '{scrap2.content}'. Anchored: {scrap2.anchor_hash[:16]}...\n")

    # 6. Moderation via Phi_C
    # Let's say scrap2 is considered spam/low quality in this context
    print(f"[Moderation] Moderating Bob's scrap...")
    print(f"  Pre-moderation visibility: {scrap2.visibility_score:.4f}")
    community.moderate_content(scrap2, [(alice, False)]) # Alice downvotes
    print(f"  Post-moderation visibility: {scrap2.visibility_score:.4f}")

    if not scrap2.is_visible():
        print(f"  -> Content hidden (Below GHOST invariant: {GHOST:.4f})")
    else:
        print(f"  -> Content still visible (Above GHOST invariant: {GHOST:.4f})")

    # 7. View Chronological Feed
    print("\n[Feed] Community Chronological Feed:")
    for s in community.get_chronological_feed():
        print(f"  - [{s.timestamp}] {s.content} (Visibility: {s.visibility_score:.4f})")

    print("\n[Seal] Canonization process complete.")
