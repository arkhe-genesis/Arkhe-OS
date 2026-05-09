import time
import numpy as np

from core.vault.participant_vault import (
    ParticipantKeyHierarchy,
    ParticipantDataVault,
    ZeroKnowledgeVaultQuery,
    HybridEncryptionMode
)
from core.multi_modal.orthogonal_witness import (
    MultiModalPhaseAligner,
    MultiModalPhaseAlignedStateVector
)
from core.vault.key_recovery_protocol import (
    ParticipantKeyRecovery,
    RecoveryShare
)
from core.protocol.meta_lattice_expansion import (
    MetaLatticeExpansion,
    TriadWitness
)

def test_vault():
    print("Testing Vault...")
    hierarchy = ParticipantKeyHierarchy("root_hash", b"master_secret")
    vault = ParticipantDataVault()
    query = ZeroKnowledgeVaultQuery(vault, hierarchy)

    hybrid = HybridEncryptionMode(pq_available=True)
    entry = hybrid.encrypt(b"test data", "purpose")
    vault.entries.append(entry)

    res = query.query("PDI > 0.9")
    assert len(res) == 1

    print("Vault OK")

def test_witness():
    print("Testing Witness...")
    aligner = MultiModalPhaseAligner("part1")
    signals = {
        "eeg": np.zeros(10),
        "fnirs": np.zeros(10),
        "hrv": np.array([1.0, 1.2]),
        "behavioral": np.zeros(10)
    }
    state = aligner.compute_multi_modal_state(signals, timestamp=time.time())
    assert state.pdi_multi > 0.0
    print("Witness OK")

def test_recovery():
    print("Testing Recovery...")
    recovery = ParticipantKeyRecovery("part1")
    recovery.setup_guardians(["g1", "g2", "g3"], 2)
    shares = recovery.generate_shares(b"secret")

    req = recovery.initiate_recovery("device_1")
    recovery.submit_share(req.request_id, shares[0])
    recovery.submit_share(req.request_id, shares[1])

    # Try finalize, should fail due to grace period
    assert recovery.finalize_recovery(req.request_id) is None

    # Veto
    assert recovery.veto_recovery(req.request_id) is True
    assert recovery.finalize_recovery(req.request_id) is None
    print("Recovery OK")

def test_expansion():
    print("Testing Expansion...")
    exp = MetaLatticeExpansion()
    aligner = MultiModalPhaseAligner("part1")
    signals = {"eeg": np.zeros(10)}
    state = aligner.compute_multi_modal_state(signals, time.time())

    exp.register_triad(("p1", "p2", "p3"), state)
    exp.register_triad(("p2", "p3", "p4"), state)

    shared = exp.find_shared_edges()
    assert ("p2", "p3") in shared

    view = exp.map_witness_to_lattice()
    assert "p4" in view["p2"]
    assert "p4" in view["p3"]
    assert "p1" not in view["p4"]
    print("Expansion OK")

if __name__ == "__main__":
    test_vault()
    test_witness()
    test_recovery()
    test_expansion()
    print("All custom tests passed.")
