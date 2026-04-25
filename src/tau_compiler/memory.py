import os
import json
import time
import logging

logger = logging.getLogger("Arkhe-Walnuts")

class WalnutMemory:
    """
    Persistência da Memória de Fase (M ∈ C).
    Armazena os estados colapsados como 'Walnuts' no diretório .alive/walnuts/
    Isto permite que a Arkhe(n) mantenha a coerência ao longo do tempo,
    lembrando-se das intenções passadas que formaram a sua estrutura atual.
    """
    def __init__(self, storage_dir=".alive/walnuts"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        self.vectors = []
        self._load_memory()

    def _load_memory(self):
        count = 0
        for filename in os.listdir(self.storage_dir):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(self.storage_dir, filename), "r") as f:
                        data = json.load(f)
                        if "state_vector" in data:
                            self.vectors.append(data["state_vector"])
                            count += 1
                except Exception as e:
                    logger.error(f"Erro ao carregar walnut {filename}: {e}")
        logger.info(f"🜏 Memória de Fase restaurada: {count} Walnuts carregados do vácuo.")

    def append(self, state_vector: list, metadata: dict):
        """Salva um novo estado na memória viva (Cristalização)."""
        self.vectors.append(state_vector)

        walnut_id = metadata.get("id", str(int(time.time() * 1000)))
        filepath = os.path.join(self.storage_dir, f"walnut_{walnut_id}.json")

        payload = {
            "timestamp": time.time(),
            "metadata": metadata,
            "state_vector": state_vector
        }

        try:
            with open(filepath, "w") as f:
                json.dump(payload, f)
            logger.debug(f"🜏 Walnut {walnut_id} cristalizado na memória.")
        except Exception as e:
            logger.error(f"Falha ao cristalizar walnut: {e}")
