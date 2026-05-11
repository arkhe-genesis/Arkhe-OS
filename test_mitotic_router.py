#!/usr/bin/env python3
"""
test_mitotic_router.py — Teste do ciclo mitótico ARKHE
Valida que um nó pode se dividir coerentemente em duas filhas.
"""
from mitotic_router import MitoticRouter

def test_full_mitotic_cycle():
    """Testa divisão completa de G1 a citocinese."""
    # Configurar nó parental
    config = {
        'node_id': 'PARENT-001',
        'colony_name': 'TestColony',
        'memory_gb': 4,
        'cpu_cores': 2,
        'bandwidth_mbps': 100,
        'storage_tb': 0.1,
    }
    parent = MitoticRouter('PARENT-001', config)

    # Executar ciclo completo
    daughter_A, daughter_B = parent.full_mitotic_cycle()

    # Verificar resultados
    assert daughter_A is not None, "Daughter A not created"
    assert daughter_B is not None, "Daughter B not created"
    assert daughter_A.node_id == 'PARENT-001-A'
    assert daughter_B.node_id == 'PARENT-001-B'

    # Verificar registro no Galactic Ledger
    galactic_events = parent.galactic.get_events_by_type("mitotic_event")
    assert len(galactic_events) == 1
    assert galactic_events[0]['parent_id'] == 'PARENT-001'
    assert galactic_events[0]['daughter_A_id'] == 'PARENT-001-A'
    assert galactic_events[0]['daughter_B_id'] == 'PARENT-001-B'

    # Verificar prova ZK
    zk_proof = galactic_events[0]['zk_proof']
    assert len(zk_proof) == 32  # SHA3-256 digest

    print("✅ Teste de ciclo mitótico completo: PASSED")
    return True
