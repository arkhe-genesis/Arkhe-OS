import unittest
from conrag.beaver import BEAVEngine
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class MockAlegacao:
    texto: str
    dominio: str
    metadados: Dict[str, Any] = field(default_factory=dict)

class TestSociologyCoxModel(unittest.TestCase):
    def setUp(self):
        self.engine = BEAVEngine()

    def test_cox_model_valid(self):
        alegacao = MockAlegacao(
            texto="Análise de sobrevivência para difusão de políticas em Recife.",
            dominio="sociology",
            metadados={
                'proportional_hazards_pvalue': 0.10, # > 0.05
                'multicollinearity_vif': 2.0, # < 5.0
                'independence_met': True,
                'linearity_met': True
            }
        )
        fatos = []
        aprovado, meta = self.engine.verify(alegacao, fatos)
        self.assertTrue(aprovado)
        self.assertEqual(meta["status"], "approved")

    def test_cox_model_invalid_proportional_hazards(self):
        alegacao = MockAlegacao(
            texto="Análise de sobrevivência para difusão de políticas.",
            dominio="sociology",
            metadados={
                'proportional_hazards_pvalue': 0.04, # <= 0.05
                'multicollinearity_vif': 2.0,
                'independence_met': True,
                'linearity_met': True
            }
        )
        fatos = []
        aprovado, meta = self.engine.verify(alegacao, fatos)
        self.assertFalse(aprovado)
        self.assertEqual(meta["status"], "blocked")

    def test_cox_model_invalid_multicollinearity(self):
        alegacao = MockAlegacao(
            texto="Análise de sobrevivência para difusão de políticas.",
            dominio="sociology",
            metadados={
                'proportional_hazards_pvalue': 0.10,
                'multicollinearity_vif': 6.0, # >= 5.0
                'independence_met': True,
                'linearity_met': True
            }
        )
        fatos = []
        aprovado, meta = self.engine.verify(alegacao, fatos)
        self.assertFalse(aprovado)
        self.assertEqual(meta["status"], "blocked")

    def test_cox_model_invalid_independence(self):
        alegacao = MockAlegacao(
            texto="Análise de sobrevivência para difusão de políticas.",
            dominio="sociology",
            metadados={
                'proportional_hazards_pvalue': 0.10,
                'multicollinearity_vif': 2.0,
                'independence_met': False, # Failed independence
                'linearity_met': True
            }
        )
        fatos = []
        aprovado, meta = self.engine.verify(alegacao, fatos)
        self.assertFalse(aprovado)
        self.assertEqual(meta["status"], "blocked")

if __name__ == '__main__':
    unittest.main()
