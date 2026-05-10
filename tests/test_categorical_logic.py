import sys
import os

from src.arkhe_core.categorical_logic import KripkeJoyalSemantics, EstimadorFunctor, LimitDiagram
from components.agi.system32.temporal.retrocausal_consistency import TemporalConsistencyOracle, TemporalMessage

class DummyLedger:
    def __init__(self):
        self.records = []
    def get_records(self, limit=None):
        return self.records
    def record(self, type, payload):
        self.records.append({'type': type, 'payload': payload, 'timestamp': payload.get('timestamp', 0)})


def test_axiomatizacao_kripke_joyal():
    topology_covers = {
        'U': [['U1', 'U2']]
    }
    sub_opens = {
        'U': ['U', 'U1', 'U2'],
        'U1': ['U1'],
        'U2': ['U2']
    }

    kj = KripkeJoyalSemantics(topology_covers, sub_opens)

    def eval_mock(node, prop, x=None):
        if x is not None:
            # P(x) is true in U1 for x=1, true in U2 for x=2
            if prop == 'P':
                if node == 'U1' and x == 1: return True
                if node == 'U2' and x == 2: return True
                return False
            if prop == 'Q':
                return True
        else:
            if prop == 'A':
                return node in ['U', 'U1']
            elif prop == 'B':
                return node in ['U2']
        return False

    assert kj.force_and('U', 'A', 'B', eval_mock) == False
    assert kj.force_and('U1', 'A', 'A', eval_mock) == True

    assert kj.force_or('U', 'A', 'B', eval_mock) == True

    assert kj.force_implies('U', 'A', 'B', eval_mock) == False
    assert kj.force_implies('U2', 'A', 'B', eval_mock) == True

    assert kj.force_not('U2', 'A', eval_mock) == True
    assert kj.force_not('U', 'A', eval_mock) == False

    # Test quantifiers
    domain = [1, 2]
    # EXISTS x P(x) on U: U is covered by {U1, U2}. U1 forces P(1). U2 forces P(2).
    assert kj.force_exists('U', 'P', domain, eval_mock) == True
    # EXISTS x P(x) on U1: U1 is covered by {U1}. U1 forces P(1).
    assert kj.force_exists('U1', 'P', domain, eval_mock) == True
    # FORALL x Q(x) on U: always true
    assert kj.force_forall('U', 'Q', domain, eval_mock) == True
    # FORALL x P(x) on U: false
    assert kj.force_forall('U', 'P', domain, eval_mock) == False


def test_preservacao_limites_estimador():
    diagram = LimitDiagram(['A', 'B', 'A'], [])
    functor = EstimadorFunctor()
    assert functor.preserves_limits(diagram) == True


def test_condicao_novikov():
    ledger = DummyLedger()
    ledger.records = [
        {
            'timestamp': 100,
            'type': 'extratemporal_message_sent',
            'payload': {
                'msg_id': 'MSG1',
                'caused_by': 'MSG2'
            }
        },
        {
            'timestamp': 101,
            'type': 'extratemporal_message_sent',
            'payload': {
                'msg_id': 'MSG2',
                'caused_by': 'MSG1'
            }
        }
    ]
    oracle = TemporalConsistencyOracle(ledger)
    msg = TemporalMessage(id='MSG1', content='test', source_timestamp=102, target_timestamp=99, sender_seal='A', receiver_seal='B')

    report = oracle.evaluate(msg)
    assert report.consistent == False
    assert report.score == 0.0
    assert report.paradox_type == "GRANDPARENT_PARADOX"
    assert "LOOP CAUSAL DETECTADO" in report.violations[0]
