import torch
import torch.nn as nn
from typing import Dict, List
import copy
from arkhe_os.crypto.hypergraph_fhe import HypergraphFHE

class FHEFederatedAggregator:
    """
    Substrato 208: FHE Federated Aggregation
    Protege embeddings e gradientes durante agregação federada via Fully Homomorphic Encryption (FHE).
    """
    def __init__(self, global_model: nn.Module, fhe_module: HypergraphFHE):
        self.global_model = global_model
        self.fhe = fhe_module
        self.encrypted_updates: List[Dict[str, torch.Tensor]] = []

    def receive_encrypted_update(self, encrypted_update: Dict[str, torch.Tensor]) -> None:
        """
        Recebe uma atualização de modelo criptografada de um cliente/nó.
        """
        self.encrypted_updates.append(encrypted_update)

    def aggregate_encrypted_updates(self) -> None:
        """
        Agrega as atualizações criptografadas de forma homomórfica, descriptografa o resultado
        final agregado e atualiza o modelo global (FedAvg).
        """
        if not self.encrypted_updates:
            return

        num_updates = len(self.encrypted_updates)

        # O FHE simula adição e nós somaremos todos os updates
        # Inicializa o acumulador com zeros, mas ele precisa estar no formato "criptografado"
        # (na nossa simulação FHE, 0 criptografado seria fhe.encrypt(0), mas vamos
        # aproveitar o primeiro update e somar o resto ou usar a matemática da simulação FHE)

        # Na nossa simulação, a soma homomórfica é enc_a + enc_b - 1000.0.
        # Portanto, agregar N elementos requer iterar.

        aggregated_enc = {}
        first_update = self.encrypted_updates[0]

        for name, param in first_update.items():
            aggregated_enc[name] = param.clone()

        for i in range(1, num_updates):
            current_update = self.encrypted_updates[i]
            for name in aggregated_enc.keys():
                # Soma homomórfica:
                aggregated_enc[name] = self.fhe.add(aggregated_enc[name], current_update[name])

        # Agora nós descriptografamos o agregado e dividimos por N
        new_state_dict = copy.deepcopy(self.global_model.state_dict())

        for name in new_state_dict.keys():
            if new_state_dict[name].dtype.is_floating_point:
                if name in aggregated_enc:
                    # Descriptografa a soma
                    decrypted_sum = self.fhe.decrypt(aggregated_enc[name])
                    # Calcula a média (FedAvg)
                    averaged_param = decrypted_sum / float(num_updates)
                    new_state_dict[name] = averaged_param

        # Carrega os novos pesos
        self.global_model.load_state_dict(new_state_dict)

        # Limpa o buffer de atualizações
        self.encrypted_updates.clear()
