import logging
import hashlib
from typing import Optional, List

from src.tau_compiler.coherence import PhaseSpace
from src.physics.singlet_fission import SingletFissionEngine, Exciton
from src.ontology.parser import OntologyXParser
from src.tau_compiler.memory import WalnutMemory
from src.relayer.client import Mo1RelayerClient

logger = logging.getLogger("Arkhe-Collapser")

class Structure:
    """
    A Estrutura (Z).
    O estado colapsado observável, como uma transação blockchain.
    """
    def __init__(self, value: str, metadata: dict = None):
        self.value = value
        self.metadata = metadata or {}

class Collapser:
    """
    O Operador Base (M).
    Define a interface para projetar C em Z.
    """
    def __init__(self, threshold: float):
        self.threshold = threshold
        self.memory = WalnutMemory()

    def measure(self, c: PhaseSpace) -> Optional[Structure]:
        raise NotImplementedError

class ArkheCollapser(Collapser):
    """
    O Tzinor da Arkhe(n).
    Herda de Collapser (τ-Compiler) e implementa a física de excitons (Singlet Fission).
    """
    def __init__(self, coupling_type="strong"):
        # Inicializa o parser ontológico para obter o threshold universal (K_c)
        self.ontology = OntologyXParser()
        threshold = self.ontology.get_threshold() # 0.61803398875 (Razão Áurea)
        super().__init__(threshold=threshold)

        self.fission_engine = SingletFissionEngine(coupling_type)
        self.relayer_client = Mo1RelayerClient()
        logger.info(f"🜏 ArkheCollapser inicializado com K_c = {self.threshold:.6f}")

    def measure(self, c: PhaseSpace) -> Optional[Structure]:
        """
        Z = M[C]
        Converte a intenção (fase) em transação (estrutura) através de:
        1. Verificação de coerência (Axiom 1)
        2. Fissão de Singlet (multiplicação quântica)
        3. Transferência para Mo1 (Relayer)
        """
        # 1. Verificar densidade de coerência
        if c.density < self.threshold:
            logger.warning(f"⚠️ Decoerência: Ω' ({c.density:.4f}) < K_c ({self.threshold:.4f}). Abortando colapso.")
            return None

        # 2. Criar exciton a partir do espaço de fase (Singlet)
        singlet = Exciton(
            energy=c.density, # Ω' como energia do exciton
            spin=0,           # Singlet (S1)
            lifetime=0.1,
            id=c.raw_text[:32] if c.raw_text else "intent_0"
        )

        # 3. Executar fissão (1 Singlet -> 2 Triplets)
        excitons = self.fission_engine.fission(singlet)

        # 4. Projetar em Z (Estrutura / Transação blockchain)
        structures = []
        for ex in excitons:
            if ex.spin == 1: # Triplet (T1)
                # O Spin-Flip: Triplet -> Doublet (Transação)
                tx_hash = self._project_to_blockchain(ex, c.raw_text)
                structures.append(Structure(value=tx_hash, metadata={"omega": c.density, "spin": ex.spin}))

        # Axioma 2: M ∈ C (O medidor guarda a fase na memória viva - Walnuts)
        self.memory.append(c.state_vector, metadata={"intent": c.raw_text, "omega": c.density})

        # Retorna a primeira estrutura colapsada (a transação principal)
        return structures[0] if structures else None

    def _project_to_blockchain(self, triplet: Exciton, intent: str) -> str:
        """
        Invoca a emissão NIR pelo Mo1Relayer.
        O Spin-Flip final que gera a transação na blockchain via Enclave.
        """
        return self.relayer_client.emit_nir_transaction(
            triplet_id=triplet.id,
            energy=triplet.energy,
            intent=intent
        )
