import unittest
from src.arkhe.layers.polyglot import PolyglotLexer, GrammarPool, TranspilerCore
from src.arkhe.layers.unix_substrate import UnixResourceManager, FdPerms, WheelerNode, SATOFrame
from src.arkhe.layers.interstellar import LaserLink, InterlinkFrame, GalacticConsensus
from src.arkhe.layers.governance import GoldenDome, MythosGate
from src.arkhe.layers.multiverse import MultiverseRouter, ConvergenceProtocol

class TestLayerIntegration(unittest.TestCase):
    def test_polyglot_transpile(self):
        pool = GrammarPool()
        lexer = PolyglotLexer(pool)
        lang = lexer.detect_language("fn main() {}")
        self.assertEqual(lang, "ark-lang")

    def test_fd_open(self):
        mgr = UnixResourceManager()
        fd = mgr.open_file("/etc/config.toml", FdPerms.READ)
        self.assertIsNotNone(fd.temporal_anchor)

    def test_laser_link_budget(self):
        budget = LaserLink.link_budget(4.24)
        self.assertIn('free_space_loss_dB', budget)

    def test_galactic_quorum(self):
        gc = GalacticConsensus()
        gc.add_message("msg1", "beacon")
        gc.confirm("msg1", "Earth", "direct")
        gc.confirm("msg1", "Lunar", "relay")
        gc.confirm("msg1", "Sol", "direct")
        res = gc.validate_message("msg1", "beacon", gc.pending_messages["msg1"]['confirmations'])
        self.assertEqual(res['status'], "AUTHENTIC")

    def test_mythos_gate_deep_space(self):
        gate = MythosGate(mode='deep_space')
        allowed = gate.evaluate_irreversible("self_destruct", {"foresight_risk": 0.9})
        self.assertFalse(allowed)

    def test_multiverse_diverge_merge(self):
        router = MultiverseRouter()
        b1 = router.create_branch()
        b2 = router.create_branch()
        protocol = ConvergenceProtocol(router)
        merged = protocol.merge(b1.id, b2.id)
        self.assertTrue(merged.id in router.branches)
        self.assertTrue(router.branches[b1.id].diverged)

if __name__ == '__main__':
    unittest.main()
