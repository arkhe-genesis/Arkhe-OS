import unittest
import numpy as np
import torch
from dataclasses import dataclass
from arkhe_os.crypto.zinc.lfir_to_ucs_compiler import LFIRtoUCSCompiler, UCSConstraint
from arkhe_os.crypto.zinc.iprs_commitment import IPRSCommitment, IPRSConfig
from arkhe_os.crypto.zinc.diffusion_proof_engine import DiffusionProofEngine, DiffusionStepWitness
from arkhe_os.crypto.zinc.meta_emergence_composer import MetaEmergenceComposer, LayerProof, MetaEmergenceProof
from arkhe_os.crypto.zinc.nostr_zinc_verifier import NostrZincVerifier

class TestZincIntegration(unittest.TestCase):

    def test_lfir_to_ucs_compiler(self):
        compiler = LFIRtoUCSCompiler()
        dummy_lfir = {
            'nodes': [{'id': 'node_1', 'line_start': 1, 'line_end': 10}],
            'edges': [{'source': 'node_1', 'target': 'node_2'}],
            'num_rows': 100,
            'num_columns': 5
        }
        ucs_instance = compiler.compile_full_instance(dummy_lfir, "source_code_placeholder")
        self.assertIn('index', ucs_instance)
        self.assertIn('constraints', ucs_instance)
        self.assertTrue(len(ucs_instance['constraints']) > 0)

    def test_iprs_commitment(self):
        config = IPRSConfig(
            base_field_prime=65537,
            code_rate=0.25,
            radix=8,
            depth=3,
            message_bit_bound=32
        )
        comm = IPRSCommitment(config)
        # 4 polynomials, degree 2
        message = np.array([
            [1, 2],
            [3, 4],
            [5, 6],
            [7, 8]
        ])
        result = comm.commit(message)
        self.assertIn("commitments", result)
        self.assertIn("openings", result)
        self.assertTrue(len(result["commitments"]) == 2)

    def test_diffusion_proof_engine(self):
        config = IPRSConfig(
            base_field_prime=65537,
            code_rate=0.25,
            radix=8,
            depth=3,
            message_bit_bound=32
        )
        engine = DiffusionProofEngine(config, latent_dim=256)
        engine.setup_projection(target_field_prime=2147483647)

        witness = DiffusionStepWitness(
            z_t=torch.randn(1, 256),
            z_t_minus_1=torch.randn(1, 256),
            context=torch.randn(1, 768),
            recurrent_state=torch.randn(1, 512),
            timestep=50,
            noise_pred=torch.randn(1, 256)
        )

        proof = engine.prove_diffusion_step(witness)
        self.assertIsNotNone(proof)
        self.assertTrue(engine.verify_proof(proof, {"timestep": 50, "latent_dim": 256}))

    def test_meta_emergence_composer(self):
        from arkhe_os.crypto.zinc.diffusion_proof_engine import ZipPlusProof
        dummy_proof = ZipPlusProof(
            commitment={},
            proof_transcript=[],
            final_opening={},
            metadata={}
        )

        layer_proofs = [
            LayerProof(layer_id="1", layer_type="code", coherence_value=0.9, proof=dummy_proof, metadata={}),
            LayerProof(layer_id="2", layer_type="data", coherence_value=0.95, proof=dummy_proof, metadata={})
        ]

        composer = MetaEmergenceComposer(emergence_threshold=0.85)
        meta_proof = composer.compose_emergence_proof(layer_proofs)
        self.assertIsNotNone(meta_proof)
        self.assertTrue(meta_proof.global_coherence > 0)
        self.assertTrue(composer.verify_meta_proof(meta_proof))

    def test_nostr_zinc_verifier(self):
        verifier = NostrZincVerifier("dummy_path")

        @dataclass
        class DummyEvent:
            content: str

        event_content = '{"proof_type": "zinc_addon", "transcript": [], "public_input": {}, "commitment_hash": "hash"}'
        event = DummyEvent(content=event_content)

        res = verifier.verify_contribution_event(event)
        self.assertTrue(res["valid"])

if __name__ == '__main__':
    unittest.main()
