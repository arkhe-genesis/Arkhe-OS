import sys
import os
import numpy as np

# Add core path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../core')))

from torsional_coherence import TorsionalCoherenceEvaluator
from spsa_adaptive import AdaptiveSPSA
from proof_tagging import ProofTagger, ProofType
from strut_weighted_louvain import StrutWeightedLouvain

def main():
    print("🧪 ARKHE OS v∞.328 — Validation Suite (OR Structure Mock)")
    print("===========================================================================")

    # 1. TorsionalCoherenceEvaluator
    evaluator = TorsionalCoherenceEvaluator(layers=12, segments=16)
    mock_state = np.random.rand(192) * 2 * np.pi
    tau = evaluator.evaluate_torsion(mock_state)
    assert len(tau) == 12, "Torsional metric should return 12 layer values"
    print("   ✅ torsional_coherence")

    # 2. AdaptiveSPSA 5 parameters
    spsa = AdaptiveSPSA(
        param_bounds=[(0.1, 2.0), (0.0001, 0.01), (0.0, 0.3), (2, 5), (0.1, 2.0)]
    )
    mock_theta = np.array([0.75, 0.003, 0.1, 3, 1.3759])
    def dummy_eval(theta):
        return 0.85
    new_theta, score = spsa.step(dummy_eval, 1, mock_theta)
    assert len(new_theta) == 5, "SPSA should optimize 5 parameters"
    print("   ✅ spsa_adaptive_5_params")

    # 3. ProofTagger
    tagger = ProofTagger()
    proof_meta = tagger.classify_proof(
        capture_fraction=0.85,
        torsional_coherence=0.9
    )
    assert proof_meta.proof_type == ProofType.TORSIONAL_STABILITY, "Proof tagger should classify as TORSIONAL_STABILITY"
    print("   ✅ proof_tagging_torsional")

    # 4. StrutWeightedLouvain
    J = np.random.randn(50, 50)
    J = (J + J.T) / 2
    struts = {(0, 1): 'H', (1, 2): 'V', (2, 3): 'D'}
    louvain = StrutWeightedLouvain()
    communities = louvain.detect_communities_weighted(J, struts)
    assert 'selected_communities' in communities, "Louvain should return selected communities"
    print("   ✅ strut_weighted_louvain")

    print("   Overall: 4/4 tests passed")

if __name__ == '__main__':
    main()
