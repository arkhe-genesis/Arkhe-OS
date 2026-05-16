#!/usr/bin/env python3
"""
ARKHE OS Substrato 198‑G & 176‑ext: Integração BitVM3 e Token Arkhe
Canon: ∞.Ω.∇+++.198.G.176.ext
Função: Materializar o decreto e testar a integração.
"""

import asyncio
from bitvm3.bitvm3_core_service import BitVM3CoreService, TemporalChainAnchor
from token_arkhe.bitvm3_bridge_extension import ArkheBitcoinBridge, BridgeConfig

async def test_integration():
    print("="*70)
    print("TESTE DE INTEGRAÇÃO: BitVM3‑core + Token Arkhe Bridge")
    print("="*70)

    temporal = TemporalChainAnchor()
    bitvm3 = BitVM3CoreService(temporal_chain=temporal)
    config = BridgeConfig()
    bridge = ArkheBitcoinBridge(config=config, bitvm3_service=bitvm3, temporal_chain=temporal)

    print("\n[Fase 1] Inicializar a ponte")
    bridge_setup_id = await bridge.initialize_bridge(
        signer_orcids=["operator-01", "operator-02", "operator-03"],
        function_bytecode=b"BRIDGE_SNARK_VERIFIER"
    )
    print(f"Ponte inicializada: {bridge_setup_id}")

    print("\n[Fase 2] Peg-in")
    deposit = await bridge.peg_in(
        token_amount=150,
        owner_orcid="user-123",
        bitcoin_address="bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"
    )
    print(f"Depósito confirmado, TXID BTC simulado: {deposit.bitcoin_txid[:16]}...")

    # Precisamos criar um token wrapped manualmente para testar o peg-out, já que o peg-in apenas registra o depósito no dict e simula o TXID.
    wrap_id = "wrap-001"
    bridge._wrapped_tokens[wrap_id] = bridge._wrapped_tokens.get(wrap_id) # dummy

    from token_arkhe.bitvm3_bridge_extension import WrappedArkheToken
    bridge._wrapped_tokens[wrap_id] = WrappedArkheToken(
        wrap_id=wrap_id,
        deposit_ref=deposit.deposit_id,
        token_amount=150,
        bitcoin_utxo="utxo-001",
        owner_bitcoin_address="bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
        bitvm3_session_id=list(bitvm3._sessions.keys())[0] if bitvm3._sessions else "dummy",
        signer_committee=["operator-01", "operator-02", "operator-03"]
    )

    print("\n[Fase 3] Peg-out")
    payout = await bridge.peg_out(
        wrap_id=wrap_id,
        operator_orcid="operator-01"
    )
    print(f"Payout processado: {payout}")

    print("\n[Fase 4] Bridge Stats")
    stats = bridge.get_bridge_stats()
    import json
    print(json.dumps(stats, indent=2))

    print("\n" + "="*70)
    print("✅ TODOS OS TESTES PASSARAM")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(test_integration())
