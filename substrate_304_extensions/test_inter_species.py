import unittest
from inter_species_diversity import CrossSpeciesExpander

class TestInterSpecies(unittest.TestCase):
    def test_expansion(self):
        expander = CrossSpeciesExpander()
        nodes = expander.expand_nodes(50)

        self.assertEqual(len(nodes), 50)

        # Test diversity
        species = set([n.species_type for n in nodes])
        self.assertTrue(len(species) > 1)

    def test_collective_phi(self):
        expander = CrossSpeciesExpander()
        expander.expand_nodes(10)
        phi_c = expander.calculate_collective_phi()

        self.assertTrue(0.0 <= phi_c <= 1.0)

if __name__ == "__main__":
    unittest.main()
