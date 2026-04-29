import os, sys, asyncio, numpy as np
sys.path.append(os.getcwd())
async def main():
    from arkhe_core.temporal_reference import TerrestrialReferenceFrame
    from arkhe_mirror.coherent_mirror import CoherentMirror
    from arkhe_crypto.dual_source_lamport import LamportNetworkQRNG, IndependentEntropySource
    from arkhe_atomic.meta_atom_fabrication import AutonomousMetaAtomFabricator, MetaAtomDesign
    from arkhe_quantum.metro_quantum_node_1d import MetroQuantumNode

    print("Verification Start")
    trf = TerrestrialReferenceFrame(); print("TRF OK")
    cm = CoherentMirror(); print("Mirror OK")
    ls = LamportNetworkQRNG("ID", None); print("Lamport OK")
    af = AutonomousMetaAtomFabricator(); print("Atomic OK")
    mq = MetroQuantumNode(); print("Quantum OK")
    print("Verification End")

if __name__ == "__main__":
    asyncio.run(main())
