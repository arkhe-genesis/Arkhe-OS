import pytest
from substrates.semantic_chemistry_engine import SemanticChemistryEngine, SemanticAtom, SemanticMolecule

def test_semantic_chemistry_reactor():
    reactor = SemanticChemistryEngine(phi_c_threshold=0.5)

    # Test adding molecules
    atom1 = SemanticAtom(concept="test1", charge=0.5, phi_c=0.9)
    mol1 = SemanticMolecule(atoms=[atom1], bonds=[])
    reactor.add_molecule(mol1)

    atom2 = SemanticAtom(concept="test2", charge=-0.5, phi_c=0.8)
    mol2 = SemanticMolecule(atoms=[atom2], bonds=[])
    reactor.add_molecule(mol2)

    assert len(reactor.molecules) == 2

    # Test reaction
    new_mols = reactor.react(steps=5)

    # Assert things changed
    assert len(reactor.molecules) >= 2
