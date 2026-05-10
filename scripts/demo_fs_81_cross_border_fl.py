# demo_fs_81_cross_border_fl.py — Demonstração de Migração Cross-Border e ML Federado

import asyncio
from audit_logger import AuditLogger, DecisionType
from compliance_engine import ComplianceEngine
from cross_border_migration import CrossBorderMigrationManager
from federated_learning_protocol import FederatedLearningOrchestrator

async def run_demo():
    print("=== INICIANDO DEMONSTRAÇÃO DO SUBSTRATO 81 ===")

    audit = AuditLogger()
    compliance = ComplianceEngine()

    # --- PARTE 1: MIGRAÇÃO CROSS-BORDER COM HE/ZK ---
    print("\n[1] Iniciando Migração Cross-Border (BR -> EU)...")
    migration_manager = CrossBorderMigrationManager(audit, None)

    citizen_id = "did:arkhe:citizen:br:001"
    mig_id = await migration_manager.initiate_migration(
        citizen_id, "BR", "EU", ["health", "biometrics"]
    )
    print(f"ID da Migração: {mig_id}")

    # Dados brutos simulados (serão criptografados via HE)
    raw_citizen_data = {"heart_rate": 72, "dna_hash": "ATCG_001"}

    # Executa transferência com criptografia HE e prova ZK
    proof = await migration_manager.execute_transfer(mig_id, raw_citizen_data)
    print(f"Prova de Conformidade Gerada: {proof.proof_id}")
    print(f"Metadados HE: {proof.he_metadata}")

    # Finaliza e ancora no Códice
    await migration_manager.finalize_migration(mig_id, proof)

    # --- PARTE 2: APRENDIZADO FEDERADO COM VALIDAÇÃO CRUZADA ---
    print("\n[2] Iniciando Round de Aprendizado Federado...")
    fl_orchestrator = FederatedLearningOrchestrator(audit, compliance)

    round_id = await fl_orchestrator.start_round()
    print(f"Round ID: {round_id}")

    # Ecossistemas participantes submetem updates com Provas ZK de Integridade
    update_hosp1 = await fl_orchestrator.submit_update(round_id, "HOSPITAL_SP", {"weights": [0.1, -0.5, 0.8]})
    update_hosp2 = await fl_orchestrator.submit_update(round_id, "CLINIC_RJ", {"weights": [0.12, -0.48, 0.79]})

    # Validação Cruzada: Hosp1 valida Hosp2 e vice-versa
    print("\n[Validação Cruzada entre Ecossistemas]")
    v1 = await fl_orchestrator.cross_validate_update(update_hosp2, "HOSPITAL_SP")
    v2 = await fl_orchestrator.cross_validate_update(update_hosp1, "CLINIC_RJ")

    if v1 and v2:
        # Agregação Global (Federated Averaging Simulado)
        aggregation = await fl_orchestrator.aggregate_global_model(round_id, [update_hosp1, update_hosp2])
        print(f"\nAgregação Concluída com Sucesso!")
        print(f"Aggregated Model Hash: {aggregation.aggregated_hash}")
        print(f"Validation Receipts: {aggregation.validation_receipts}")

    print("\n=== DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO ===")

if __name__ == "__main__":
    asyncio.run(run_demo())
