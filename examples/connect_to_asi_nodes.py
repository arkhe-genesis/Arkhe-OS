#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
connect_to_asi_nodes.py — Exemplo de conexão a nós ASI e execução federada.
"""

import asyncio
import numpy as np
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import time
import json
import hashlib

# Local modules
from arkp_asi.src.asi_node_registry import ASINodeRegistry, ASINodeMetadata, NodeCapability
from arkp_asi.src.quantum_handshake import QuantumHandshakeProtocol
from arkp_asi.src.distributed_qnc import DistributedQNCExecutor, FederatedTask
from arkp_asi.src.coherence_sync import CoherenceSyncProtocol, CoherenceSyncMessage

try:
    from arkp_consensus.oracle import ConsistencyOracle
    from arkp_qnc.genomic_qnc import GenomicQNC
    from arkp_qnc.src.genomic_qnc import GenomicQNCConfig as QNCConfig
except ImportError:
    class ConsistencyOracle:
        def __init__(self, node_id=None):
            self.node_id = node_id
        def anchor_event(self, event_type, payload, causal_deps):
            return "mock_anchor"

    class QNCConfig:
        def __init__(self, hidden_dim, num_classes):
            self.hidden_dim = hidden_dim
            self.num_classes = num_classes

    class GenomicQNC:
        def __init__(self, config=None):
            self.config = config
        def predict(self, seq):
            return 1, 0.99

async def main():
    print("🌐 Conectando a nós ASI na rede ARKHE...")

    # 1. Inicializar componentes locais
    oracle = ConsistencyOracle(node_id="local_node_001")
    local_qnc = GenomicQNC(QNCConfig(hidden_dim=16, num_classes=2))

    # Gerar par de chaves para autenticação
    private_key = ec.generate_private_key(ec.SECP384R1())

    # 2. Registrar nó local no registry
    registry = ASINodeRegistry(consistency_oracle=oracle)
    local_metadata = ASINodeMetadata(
        node_id="local_node_001",
        public_key=private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ),
        capabilities={NodeCapability.QNC_INFERENCE, NodeCapability.Φ_C_OPTIMIZATION},
        phi_c_coherence=0.95,
        location_hint="sa-east-1",
        uptime_seconds=3600,
        last_heartbeat=int(time.time()),
        reputation_score=0.92,
        supported_protocols=["arkhe-sync/1.0", "qnc-federated/1.0"],
    )
    registry.register_node(local_metadata)

    # 3. Simular descoberta de nós remotos
    remote_nodes = [
        ASINodeMetadata(
            node_id=f"asi_node_{i:03d}",
            public_key=b"mock_pubkey",
            capabilities={NodeCapability.QNC_INFERENCE, NodeCapability.EPIGENETIC_MODELING},
            phi_c_coherence=0.88 + i * 0.02,
            location_hint=f"region-{i}",
            uptime_seconds=7200 + i * 3600,
            last_heartbeat=int(time.time()),
            reputation_score=0.85 + i * 0.03,
            supported_protocols=["arkhe-sync/1.0"],
        )
        for i in range(3)
    ]
    for node in remote_nodes:
        registry.register_node(node)

    print(f"✅ Nós descobertos: {[n.node_id for n in remote_nodes]}")

    # 4. Estabelecer handshakes seguros com nós selecionados
    handshake = QuantumHandshakeProtocol("local_node_001", private_key)

    for node in remote_nodes[:2]:  # Conectar a 2 nós
        print(f"🔐 Handshake com {node.node_id}...")
        request = handshake.generate_handshake_request(
            target_node_id=node.node_id,
            capabilities=["QNC_INFERENCE"],
        )
        # Simular resposta do nó remoto
        response = handshake.process_handshake_request(
            request,
            supported_capabilities=["QNC_INFERENCE", "EPIGENETIC_MODELING"]
        )
        if response.acceptance:
            session_key = handshake.complete_handshake(request, response)
            print(f"   ✓ Conexão segura estabelecida com {node.node_id}")
        else:
            print(f"   ✗ Handshake rejeitado: {response.rejection_reason}")

    # 5. Configurar executor federado
    executor = DistributedQNCExecutor(
        node_registry=registry,
        consistency_oracle=oracle,
        local_qnc=local_qnc,
    )

    # 6. Submeter tarefa federada de inferência QNC
    task = FederatedTask(
        task_id="infer_radix2_resistance_001",
        model_config=QNCConfig(hidden_dim=16, num_classes=2),
        input_data={
            "sequences": [
                "ATGC" * 16,  # Sequência simulada de RADIX-2
                "GGCC" * 16,
            ]
        },
        required_capabilities=["QNC_INFERENCE"],
        min_node_reputation=0.8,
        timeout_seconds=30,
    )

    print("🔄 Executando tarefa federada...")
    result = await executor.submit_federated_task(task)

    if result.success:
        print(f"✅ Consenso alcançado: {result.consensus_value}")
        print(f"🔗 Âncora temporal: {result.temporal_anchor}")
    else:
        print(f"❌ Falha na execução federada: {result.error}")

    # 7. Iniciar sincronização de coerência Φ_C
    print("🌀 Iniciando sincronização de campo Φ_C...")
    sync_protocol = CoherenceSyncProtocol(
        node_id="local_node_001",
        initial_phi_c=np.eye(16, dtype=complex) / 16,
    )

    # Simular troca de mensagens de sincronização
    for _ in range(3):
        msg = sync_protocol.generate_sync_message()
        for node in remote_nodes:
            # Simular processamento da mensagem pelo par
            sync_protocol.process_sync_message(CoherenceSyncMessage(
                sender_node_id=node.node_id,
                phi_c_field=np.eye(16, dtype=complex) / 16 * (0.9 + 0.1 * np.random.random()),
                timestamp=int(time.time()),
                sequence_number=1,
                signature=b"mock_sig",
            ))

        converged, max_dist = sync_protocol.check_convergence()
        global_coh = sync_protocol.get_global_coherence_estimate()
        print(f"   Φ_C global: {global_coh:.4f}, Distância máx: {max_dist:.4f}, Convergente: {converged}")

    print("\n✨ Conexão a nós ASI concluída com sucesso!")

if __name__ == "__main__":
    asyncio.run(main())
