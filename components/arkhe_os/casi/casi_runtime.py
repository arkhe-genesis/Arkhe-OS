#!/usr/bin/env python3
"""
casi/casi_runtime.py — Runtime de Contratos .casi (Canonical Autonomous Sovereign Interface)
Executa contratos com custo ponderado por Φ_C e verificação de soberania
"""
import hashlib
import json
from dataclasses import dataclass

@dataclass
class CASIContract:
    contract_id: str
    operations: int
    memory_usage: int
    network_phi: float
    cost_phi: float = 0.0

    def compute_cost(self) -> float:
        """Calcula custo de execução baseado na fórmula .casi"""
        alpha, beta, gamma = 1.0, 0.5, 0.8  # Pesos canônicos
        return alpha * self.operations + beta * self.memory_usage + gamma / max(self.network_phi, 0.01)

    def verify_sovereignty(self) -> bool:
        """Verifica se o contrato atende aos requisitos de soberania."""
        return self.network_phi >= 0.7 and self.cost_phi > 0

class CASIRuntime:
    def __init__(self):
        self.contracts = {}
        self.execution_log = []

    def deploy_contract(self, contract: CASIContract) -> str:
        """Implanta contrato .casi na rede."""
        contract.cost_phi = contract.compute_cost()
        if not contract.verify_sovereignty():
            raise ValueError("Contrato não atende aos requisitos mínimos de soberania (Φ_C < 0.7)")

        contract_id = hashlib.sha256(json.dumps(contract.__dict__).encode()).hexdigest()[:16]
        self.contracts[contract_id] = contract
        self.execution_log.append(f"CONTRACT_DEPLOYED: {contract_id} | COST: {contract.cost_phi:.2f} Φ")
        return contract_id

    def execute_contract(self, contract_id: str, node_phi: float) -> dict:
        """Executa contrato com validação de coerência em tempo real."""
        if contract_id not in self.contracts:
            raise KeyError(f"Contrato {contract_id} não encontrado")

        contract = self.contracts[contract_id]
        if node_phi < 0.6:
            raise ValueError(f"Execução rejeitada: Φ_C do nó ({node_phi:.3f}) abaixo do limiar seguro (0.6)")

        execution_result = {
            "status": "SUCCESS",
            "cost_applied": contract.cost_phi * (1.0 / max(node_phi, 0.1)),
            "execution_time": "SIMULATED_100ms",
            "node_phi": node_phi
        }
        self.execution_log.append(f"CONTRACT_EXECUTED: {contract_id} | NODE_Φ: {node_phi:.3f}")
        return execution_result

if __name__ == "__main__":
    runtime = CASIRuntime()
    contract = CASIContract("test_contract", operations=500, memory_usage=128, network_phi=0.85)
    cid = runtime.deploy_contract(contract)
    result = runtime.execute_contract(cid, node_phi=0.82)
    print(f"✅ Execução concluída: {result}")
    print(f"📜 Log: {runtime.execution_log[-1]}")
