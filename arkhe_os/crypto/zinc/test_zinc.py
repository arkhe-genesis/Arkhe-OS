import unittest
import torch
import numpy as np
from arkhe_os.crypto.zinc import (
    LFIRtoUCSCompiler, IPRSConfig, IPRSCommitment,
    DiffusionStepWitness, DiffusionProofEngine,
    LayerProof, MetaEmergenceProof, MetaEmergenceComposer,
    NostrZincVerifier
)

class TestZincIntegration(unittest.TestCase):
    def test_lfir_to_ucs(self):
        compiler = LFIRtoUCSCompiler()
        graph = {"nodes": [{"id": 1}], "edges": [], "num_rows": 100, "num_columns": 10}
        instance = compiler.compile_full_instance(graph, "test code")
        self.assertIn("index", instance)
        self.assertIn("constraints", instance)

    def test_iprs_commitment(self):
        config = IPRSConfig(base_field_prime=65537, code_rate=0.25, radix=2, depth=2, message_bit_bound=32)
        comm = IPRSCommitment(config)
        msg = np.array([[1, 2], [3, 4]])
        result = comm.commit(msg)
        self.assertIn("commitments", result)

    def test_diffusion_proof(self):
        config = IPRSConfig(base_field_prime=65537, code_rate=0.25, radix=2, depth=2, message_bit_bound=32)
        engine = DiffusionProofEngine(config, latent_dim=16)
        engine.setup_projection(17)
        witness = DiffusionStepWitness(
            z_t=torch.randn(1, 16),
            z_t_minus_1=torch.randn(1, 16),
            context=torch.randn(1, 16),
            recurrent_state=torch.randn(1, 16),
            timestep=10,
            noise_pred=torch.randn(1, 16)
        )
        proof = engine.prove_diffusion_step(witness)
        self.assertTrue(engine.verify_proof(proof, {"timestep": 10, "latent_dim": 16}))

    def test_meta_emergence(self):
        # Dummy proof
        proof = type('MockProof', (), {'commitment': {}, 'proof_transcript': [], 'final_opening': {}, 'metadata': {}})()
        lp = LayerProof("layer_id", "code", 0.95, proof, {})
        composer = MetaEmergenceComposer(emergence_threshold=0.90)
        meta_proof = composer.compose_emergence_proof([lp])
        self.assertTrue(composer.verify_meta_proof(meta_proof))

if __name__ == '__main__':
    unittest.main()
