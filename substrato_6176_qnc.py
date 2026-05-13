from src.arkhe.layers.qnc_expanded import GenomicEmbedding, PhiCGatedAttention
from arkp_sigha.sigha_core import FisherBuresManifold, NaturalGradientFlow
from src.arkhe.layers.qnc_transfer import MultiSpeciesQNC
import numpy as np

def run_tests():
    print("Testing MultiSpeciesQNC...")
    model = MultiSpeciesQNC(max_len=10, hidden_dim=4)
    # create some dummy data
    species_data = {
        "OrganismA": [("ATGCATGCAT", 1), ("ATGCATGCAT", 1)],
        "OrganismB": [("AAAAATGCAT", 0), ("AAAAATGCAT", 0)]
    }
    loss_history = model.pretrain_on_all_species(species_data, epochs=5, lr=0.1)
    print("Pretraining loss history:", loss_history)
    print("Success")

if __name__ == "__main__":
    run_tests()
