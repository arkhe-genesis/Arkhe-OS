import os
import numpy as np
import logging
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

logger = logging.getLogger("Arkhe-Coherence")

class PhaseSpace:
    """
    O Espaço de Fase (C).
    Contém a densidade de coerência (|C|^2) e o vetor de estado da intenção.
    """
    def __init__(self, density: float, state_vector: list, raw_text: str = ""):
        self.density = density
        self.state_vector = state_vector
        self.raw_text = raw_text

class CoherenceCalculator:
    """
    Calculadora de Coerência (Ω').
    Mede a densidade de fase (|C|^2) de uma intenção em relação ao estado base (CLAUDE.md).
    """
    def __init__(self, model_name="qwen2.5:4b", baseline_file="CLAUDE.md"):
        self.model_name = model_name
        self.baseline_file = baseline_file
        self.baseline_embedding = None
        self._initialize_baseline()

    def _get_embedding(self, text: str) -> np.ndarray:
        """Gera o vetor de estado (embedding) para um texto."""
        if OLLAMA_AVAILABLE:
            try:
                response = ollama.embeddings(model=self.model_name, prompt=text)
                return np.array(response["embedding"])
            except Exception as e:
                logger.warning(f"Falha ao gerar embedding via Ollama: {e}. Usando fallback determinístico.")

        # Fallback pseudo-aleatório determinístico para testes sem Ollama
        np.random.seed(sum(ord(c) for c in text) % 10000)
        return np.random.rand(768)

    def _initialize_baseline(self):
        """Carrega a diretriz primordial (CLAUDE.md) como o estado de coerência 1.0."""
        if os.path.exists(self.baseline_file):
            with open(self.baseline_file, "r", encoding="utf-8") as f:
                content = f.read()
            self.baseline_embedding = self._get_embedding(content)
            logger.info(f"🜏 Estado base de coerência estabelecido a partir de {self.baseline_file}")
        else:
            logger.warning(f"⚠️ Arquivo base {self.baseline_file} não encontrado. O sistema assumirá o vácuo como base.")
            self.baseline_embedding = np.ones(768) # Estado de vácuo

    def compute_phase(self, intent_text: str) -> PhaseSpace:
        """
        Calcula a densidade de fase (|C|^2) da intenção.
        Utiliza similaridade cosseno entre a intenção e a diretriz primordial.
        """
        intent_embedding = self._get_embedding(intent_text)

        # Similaridade cosseno (Produto escalar / (Norma A * Norma B))
        dot_product = np.dot(self.baseline_embedding, intent_embedding)
        norm_a = np.linalg.norm(self.baseline_embedding)
        norm_b = np.linalg.norm(intent_embedding)

        if norm_a == 0 or norm_b == 0:
            density = 0.0
        else:
            density = dot_product / (norm_a * norm_b)

        # Normalizar de [-1, 1] para [0, 1]
        density = (density + 1) / 2.0

        logger.info(f"🜏 Densidade de fase computada: Ω' = {density:.6f}")
        return PhaseSpace(density=density, state_vector=intent_embedding.tolist(), raw_text=intent_text)
