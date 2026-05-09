from typing import Dict

from ..oracles.physics import PhysicsOracle
from ..oracles.biology import BiologyOracle
from ..oracles.tech import TechOracle
from ..oracles.social import SocialOracle
from ..oracles.econ import EconOracle

class PolymathEvaluator:
    def evaluate(self, proposal: Dict) -> Dict[str, float]:
        scores = {}
        # 1. Avaliação física (se aplicável): usa Substratos 122 (hopfion), 5021 (time crystal)
        scores['physics'] = PhysicsOracle.assess(proposal.get('physics_claims'))
        # 2. Avaliação biológica: Substratos 701 (NICE), 5017 (Orch-Φ)
        scores['biology'] = BiologyOracle.assess(proposal.get('bio_claims'))
        # 3. Avaliação tecnológica: Substratos 5015 (ONNX), 5004 (LeWorldModel)
        scores['tech'] = TechOracle.assess(proposal.get('tech_stack'))
        # 4. Avaliação social: Substratos 5011 (ASI Social), 5020 (Egregore)
        scores['social'] = SocialOracle.assess(proposal.get('social_impact'))
        # 5. Avaliação econômica: Substratos 344 (Φ-REP), 5018 (Sovereign Pip)
        scores['economic'] = EconOracle.assess(proposal.get('business_model'))
        return scores