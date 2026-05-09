import os
import json
import time
import logging
from typing import Dict, Any, List

# Configurar logging para evitar chamadas duplicadas ao basicConfig em construtores
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class WalnutMemory:
    """
    Persistência da Memória de Fase (M ∈ C).
    Armazena os estados colapsados como 'Walnuts' no diretório .alive/walnuts/
    """
    def __init__(self, storage_dir=".alive/walnuts"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        self.vectors = []
        self._load_memory()
        self.logger = logging.getLogger("Arkhe-Walnuts")

    def _load_memory(self):
        count = 0
        if os.path.exists(self.storage_dir):
            for filename in os.listdir(self.storage_dir):
                if filename.endswith(".json"):
                    try:
                        with open(os.path.join(self.storage_dir, filename), "r") as f:
                            data = json.load(f)
                            if "state_vector" in data:
                                self.vectors.append(data["state_vector"])
                                count += 1
                    except Exception as e:
                        print(f"Erro ao carregar walnut {filename}: {e}")
        # logging here might fail if called before basicConfig, so we use print or wait

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
        except Exception as e:
            self.logger.error(f"Falha ao cristalizar walnut: {e}")
