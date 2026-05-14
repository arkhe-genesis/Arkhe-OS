#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
substrato_9018_timechain.py — Substrato 9018: TemporalChain Core Independente
Demonstração e entrypoint para o ecossistema Arkhe.
"""

import asyncio
from arkhe_timechain.core import TemporalChain, EventType
from arkhe_timechain.ma_s2_integration import MA_S2_TimechainIntegration
import os
import json

async def run_demo():
    print("⏳ Inicializando Substrato 9018: Timechain...")

    # Usar banco em memória / arquivo temporário para a demo
    if os.path.exists("demo_timechain.db"):
        os.remove("demo_timechain.db")

    tc = TemporalChain(storage_backend="sqlite", storage_config={"path": "demo_timechain.db"})

    print(f"✅ Cadeia inicializada. Selo gênese: {tc.current_seal[:16]}...")

    print("\n📝 Ancorando evento de gênese...")
    anchor1 = await tc.anchor_event(
        event_type=EventType.CUSTOM,
        payload={"action": "chain_init", "version": "1.0.0"},
        metadata={"initialized_by": "demo"}
    )
    print(f"   ID: {anchor1.event.event_id}")
    print(f"   Selo: {anchor1.event.seal[:16]}...")
    print(f"   Cadeia: {anchor1.chain_seal[:16]}...")

    print("\n🔍 Registrando controle MA-S2...")
    mas2 = MA_S2_TimechainIntegration(tc)
    seal_mas2 = await mas2.log_control_execution(
        control_id="CVS-0.1",
        execution_result={"status": "compliant", "vulnerabilities": 0},
        metadata={"scan_target": "arkhe_core"},
        causal_deps=[anchor1.event.event_id]
    )
    print(f"   Selo MA-S2: {seal_mas2[:16]}...")

    print("\n📊 Gerando Prova de Conformidade...")
    proof = await mas2.generate_compliance_proof(["CVS-0.1"])
    print(f"   Eventos encontrados: {proof['event_count']}")
    print(f"   Raiz Merkle: {proof['merkle_proof']['root'][:16]}..." if proof.get('merkle_proof') else "   Raiz Merkle: N/A")

    print("\n✅ Verificando Integridade da Cadeia...")
    is_valid = await tc.verify_chain()
    print(f"   Cadeia Íntegra: {is_valid}")
    print(f"   Total de Eventos: {tc.event_count}")

    print("\n🎉 Demonstração do Substrato 9018 Concluída com Sucesso!")

if __name__ == "__main__":
    asyncio.run(run_demo())
