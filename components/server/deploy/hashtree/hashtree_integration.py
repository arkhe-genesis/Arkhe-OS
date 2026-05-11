import subprocess
import json
from typing import Dict, Optional
import hashlib

class HashtreeArkheBridge:
    """
    Ponte entre Arkhe(n) e Hashtree P2P.
    """
    
    def __init__(self, htree_cli_path: str = "htree"):
        self.cli = htree_cli_path
        self._initialized = False
        
    def initialize(self, npub: Optional[str] = None):
        """
        Inicializa o nó Hashtree.
        """
        # Iniciar daemon
        subprocess.run([self.cli, "start", "--daemon"], check=True)
        
        # Configurar identidade
        if npub:
            subprocess.run([self.cli, "user", "--set", npub], check=True)
        
        self._initialized = True
    
    def publish_resonance_proof(self, 
                                 phase: float, 
                                 omega_prime: float,
                                 nonce: int,
                                 hash_proof: str) -> str:
        """
        Publica prova de ressonância no Hashtree.
        Retorna nhash permalink.
        """
        proof_data = {
            "phase": phase,
            "omega_prime": omega_prime,
            "nonce": nonce,
            "hash": hash_proof,
            "timestamp": int(np.datetime64('now').astype('datetime64[s]').astype(int)),
            "mydland_constants": {
                "k1": 0.015311,
                "k2": 0.05200,
                "k3": 0.233,
                "k4": 0.09778
            }
        }
        
        # Salvar prova
        proof_file = f"/tmp/resonance_proof_{nonce}.json"
        with open(proof_file, 'w') as f:
            json.dump(proof_data, f)
        
        # Adicionar ao Hashtree
        result = subprocess.run(
            [self.cli, "add", proof_file],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Extrair CID/nhash
        lines = result.stdout.strip().split('\n')
        nhash = lines[-1] if lines else None
        
        return nhash
    
    def get_resonance_proof(self, nhash: str) -> Dict:
        """
        Recupera prova de ressonância do Hashtree.
        """
        result = subprocess.run(
            [self.cli, "cat", nhash],
            capture_output=True,
            text=True,
            check=True
        )
        
        return json.loads(result.stdout)
    
    def sync_peer_state(self) -> Dict:
        """
        Sincroniza estado com peers via Hashtree.
        """
        result = subprocess.run(
            [self.cli, "status"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse status
        status = {}
        for line in result.stdout.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                status[key.strip()] = value.strip()
        
        return status
