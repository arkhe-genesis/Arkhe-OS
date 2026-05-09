# examples/cross_chain_bridge_demo.py
"""
Exemplo: Transação cross-chain entre Ethereum (PoS) e Cosmos Hub (BFT).
"""
from arkhe_os.orchestrator import (
    MultiConsensusBridge, BlockchainConfig, ConsensusType,
    CrossChainTransaction
)

async def main():
    # 1. Configurar blockchains para interoperabilidade
    blockchain_configs = {
        "ethereum-mainnet": BlockchainConfig(
            chain_id="ethereum-mainnet",
            consensus_type=ConsensusType.POS,
            validation_logic="cid:QmEthPoSValidatorV2...",
            finality_time=12.0,  # ~12 segundos para finalidade em Ethereum PoS
            bridge_enabled=True
        ),
        "cosmos-hub": BlockchainConfig(
            chain_id="cosmos-hub",
            consensus_type=ConsensusType.BFT,
            validation_logic="cid:QmCosmosBFTValidatorV1...",
            finality_time=6.0,  # ~6 segundos para finalidade em Tendermint
            bridge_enabled=True
        )
    }

    bridge = MultiConsensusBridge(blockchain_configs)

    # 2. Preparar payload da transação (ex: transferência de Φ‑tokens)
    payload = {
        "action": "transfer",
        "token": "PHI",
        "amount": 100.0,
        "from": "0xAbC...123",  # Ethereum address
        "to": "cosmos1xyz...789",  # Cosmos address
        "memo": "Cross-chain coherence incentive"
    }
    import json
    payload_bytes = json.dumps(payload, sort_keys=True).encode()

    # 3. Obter proof de validade na Ethereum (simulado)
    # Em produção: gerar proof via Ethereum light client + Merkle proof
    source_proof = {
        "proof_id": "eth_proof_abc123",
        "block_hash": "0x7f3a9c2e...",
        "tx_index": 42,
        "merkle_proof": ["0x...", "0x...", "..."],
        "consensus_proof": {
            "type": "pos_finality",
            "validator_set_hash": "0x...",
            "signature_aggregate": "0x..."
        }
    }

    # 4. Iniciar transação cross-chain
    tx = bridge.initiate_cross_chain_tx(
        source_chain="ethereum-mainnet",
        target_chain="cosmos-hub",
        payload=payload_bytes,
        source_validation_proof=source_proof
    )
    print(f"🌉 Transação cross-chain iniciada: {tx.tx_id}")
    print(f"   Origem: {tx.source_chain} (PoS)")
    print(f"   Destino: {tx.target_chain} (BFT)")
    print(f"   Status: {tx.status}")

    # 5. Executar ponte: validar em Cosmos e completar transferência
    completed_tx = bridge.execute_bridge(tx.tx_id)

    if completed_tx and completed_tx.status == "completed":
        print(f"✅ Ponte concluída com sucesso!")
        print(f"   Target proof ID: {completed_tx.target_proof['proof_id']}")
        print(f"   Finalized at: {completed_tx.metadata.get('bridge_completed_at')}")

        # 6. Registrar evento de bridge no ledger federado (Substrato 287)
        # (implementação via adapter do Substrato 287)

    else:
        print(f"❌ Falha na ponte: {completed_tx.metadata.get('failure_reason', 'unknown') if completed_tx else 'unknown'}")

    return completed_tx

if __name__ == "__main__":
    import asyncio
    import json
    asyncio.run(main())
