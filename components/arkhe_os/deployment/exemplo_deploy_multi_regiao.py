"""
Exemplo completo: Deploy ARKHE OS para pesquisa clínica internacional
com compliance automático para HIPAA (US), GDPR (EU), e ANVISA/LGPD (BR).
"""
import sys
import os

# Add arkhe_os root to sys.path if not running from there
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from datetime import datetime
from arkhe_os.deployment.compliance.engine import ComplianceEngine, DeploymentConfig
from arkhe_os.deployment.orchestrator.infrastructure import (
    DeploymentStack, Resource, ResourceType
)
from arkhe_os.deployment.orchestrator.deployer import DeploymentDeployer
from arkhe_os.deployment.audit.ledger import AuditLedger

async def main():
    # 1. Inicializar componentes
    compliance_engine = ComplianceEngine()
    audit_ledger = AuditLedger(ledger_path="./audit_logs/", signing_key="prod_key_***")
    deployer = DeploymentDeployer(compliance_engine, audit_ledger)

    # 2. Definir configuração de deployment
    config = DeploymentConfig(
        deployment_id="arkhe_nafld_international_v1",
        regions=["us-east-1", "eu-west-1", "sa-east-1"],
        data_classification={
            "phi": True,      # Protected Health Information (HIPAA)
            "pii": True,      # Personal Identifiable Information (GDPR/LGPD)
            "research": True, # Dados de pesquisa clínica
        },
        encryption={
            "at_rest": True,
            "algorithm": "AES-256-GCM",
            "fhe_enabled": True,  # Para computação em Φ_C sem expor dados brutos
            "in_transit": True,
            "protocol": "TLS-1.3",
            "pqc_signatures": True,  # Assinaturas pós-quânticas para qhttp://
        },
        access_control={
            "unique_user_ids": True,
            "role_based": True,
            "consent_granular": True,  # Consentimento por estudo/campo (Substrato 287)
            "audit_logging": True,
        },
        audit={
            "enabled": True,
            "immutable": True,
            "retention_days": 2555,
            "checksums": True,
            "versioning": True,
            "zk_proofs": True,  # Proofs de compliance sem revelar dados
        },
        integrity={
            "checksums": True,
            "versioning": True,
        },
        retention={
            "phi": 2555,    # 7 anos
            "pii": 2555,    # 7 anos (GDPR permite menos, mas usamos máximo)
            "research": 3650,  # 10 anos para integridade de pesquisa
        },
    )

    # 3. Definir stack de infraestrutura
    stack = DeploymentStack(
        stack_id="arkhe_nafld_infra",
        deployment_name="ARKHE OS - NAFLD International Study",
        jurisdictions=["hipaa_us", "gdpr_eu", "anvisa_brazil", "lgpd_brazil"],
        resources=[
            # Storage para dados sensíveis (US)
            Resource(
                resource_id="phi_storage_us",
                resource_type=ResourceType.STORAGE,
                provider="aws",
                region="us-east-1",
                config={
                    "type": "s3",
                    "encryption_enabled": True,
                    "encryption_algorithm": "AES-256-GCM",
                    "versioning": True,
                    "audit_logging_enabled": True,
                    "log_retention_days": 2555,
                },
                compliance_tags={"hipaa": "eligible", "gdpr": "adequate"},
                encryption_required=True,
            ),
            # Compute para processamento (EU)
            Resource(
                resource_id="compute_eu",
                resource_type=ResourceType.COMPUTE,
                provider="azure",
                region="eu-west-1",
                config={
                    "type": "confidential_vm",  # VMs com enclaves para FHE
                    "fhe_enabled": True,
                    "audit_logging_enabled": True,
                    "network_isolation": True,
                },
                compliance_tags={"gdpr": "adequate", "hipaa": "eligible"},
                encryption_required=True,
            ),
            # Database para metadados (BR)
            Resource(
                resource_id="metadata_db_br",
                resource_type=ResourceType.DATABASE,
                provider="gcp",
                region="sa-east-1",
                config={
                    "type": "cloud_sql_postgres",
                    "encryption_enabled": True,
                    "audit_logging_enabled": True,
                    "log_retention_days": 2555,
                    "point_in_time_recovery": True,
                },
                compliance_tags={"anvisa": "compliant", "lgpd": "adequate"},
                encryption_required=True,
            ),
            # Key management multi-região
            Resource(
                resource_id="kms_multi_region",
                resource_type=ResourceType.KEY_MANAGEMENT,
                provider="aws",
                region="us-east-1",  # Primary, com replicas
                config={
                    "type": "cloudhsm",
                    "multi_region": True,
                    "pqc_algorithms": ["CRYSTALS-Dilithium", "SPHINCS+"],
                    "audit_logging_enabled": True,
                },
                compliance_tags={"hipaa": "eligible", "gdpr": "adequate", "anvisa": "compliant"},
                encryption_required=True,
            ),
        ],
    )

    # 4. Executar deployment com validação de compliance
    print("🚀 Iniciando deployment com validação regulatória...")
    result = await deployer.deploy(stack, config)

    # 5. Exibir resultados
    print(f"\n📊 Resultado do Deployment: {result['status']}")

    if result["status"] == "SUCCESS":
        print(f"✅ Deployment ID: {result['deployment_id']}")
        print("\n🔐 Compliance Summary:")
        for jur, summary in result["compliance_summary"].items():
            proof = summary.get("proof", "N/A")[:16] + "..." if summary.get("proof") else "Pending"
            print(f"   • {jur.upper()}: {summary['status']} (Proof: {proof})")

        print("\n📋 Próximos passos:")
        print("   1. Configurar acesso de pesquisadores via Patient Vault (Substrato 287)")
        print("   2. Integrar com Clinical Trial Simulator (Substrato 286)")
        print("   3. Habilitar Cross-Species Mapping (Substrato 288)")
        print("   4. Agendar auditoria periódica com relatórios ZK-verificáveis")

    else:
        print(f"❌ Falha: {result.get('reason')}")
        if "details" in result:
            print("\n🔍 Detalhes das violações:")
            for jur, report in result["details"].items():
                if report["compliance_status"] == "NON_COMPLIANT":
                    print(f"\n   {jur.upper()}:")
                    for v in report.get("violations", []):
                        print(f"   • [{v['severity']}] {v['description']}")
                        print(f"     → Correção: {v['remediation']}")

    # 6. Gerar relatório de auditoria inicial
    print("\n📄 Gerando relatório de auditoria inicial...")
    report = audit_ledger.generate_compliance_report(
        jurisdiction="multi",
        time_range=("2026-01-01T00:00:00Z", datetime.now().isoformat()),
    )

    print(f"✅ Relatório gerado: {len(report['compliance_proofs'])} proofs de compliance")
    print(f"🔗 Integridade do ledger: {'✅ Verificada' if report['integrity_verification']['valid'] else '❌ Falha'}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
