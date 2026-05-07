"""
Definição declarativa de infraestrutura com validação regulatória integrada.
Estilo Terraform/CDK, mas com compliance-by-design.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

class ResourceType(Enum):
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    DATABASE = "database"
    KEY_MANAGEMENT = "key_management"
    AUDIT_LOG = "audit_log"

@dataclass
class Resource:
    """Recurso de infraestrutura com metadados regulatórios."""
    resource_id: str
    resource_type: ResourceType
    provider: str  # Ex: "aws", "azure", "gcp", "on-premise"
    region: str
    config: Dict[str, Any]
    compliance_tags: Dict[str, str] = field(default_factory=dict)  # Ex: {"hipaa": "eligible", "gdpr": "adequate"}
    encryption_required: bool = False
    audit_logging: bool = True

    def validate_compliance(self, jurisdiction: str) -> tuple[bool, List[str]]:
        """Valida recurso contra regras de uma jurisdição."""
        errors = []

        if self.encryption_required:
            if not self.config.get("encryption_enabled"):
                errors.append(f"{self.resource_id}: Encryption required but not enabled")
            if self.config.get("encryption_algorithm") not in ["AES-256-GCM", "ChaCha20-Poly1305"]:
                errors.append(f"{self.resource_id}: Weak encryption algorithm")

        if self.audit_logging:
            if not self.config.get("audit_logging_enabled"):
                errors.append(f"{self.resource_id}: Audit logging required but not enabled")
            if self.config.get("log_retention_days", 0) < 2555:  # 7 anos para HIPAA
                errors.append(f"{self.resource_id}: Log retention below regulatory minimum")

        # Verificar tags de compliance
        if jurisdiction in self.compliance_tags:
            if self.compliance_tags[jurisdiction] not in ["eligible", "certified", "adequate", "compliant"]:
                errors.append(f"{self.resource_id}: Not compliant with {jurisdiction}")

        return len(errors) == 0, errors

@dataclass
class DeploymentStack:
    """Pilha de recursos para deployment com validação regulatória."""
    stack_id: str
    deployment_name: str
    resources: List[Resource]
    jurisdictions: List[str]  # Jurisdições regulatórias aplicáveis
    compliance_requirements: Dict[str, List[str]] = field(default_factory=dict)

    def validate_all(self) -> Dict[str, List[str]]:
        """Valida todos os recursos contra todas as jurisdições."""
        results = {}

        for jurisdiction in self.jurisdictions:
            errors = []
            for resource in self.resources:
                valid, resource_errors = resource.validate_compliance(jurisdiction)
                if not valid:
                    errors.extend(resource_errors)
            results[jurisdiction] = errors

        return results

    def generate_terraform(self) -> str:
        """Gera código Terraform a partir da stack (exemplo simplificado)."""
        tf_blocks = []

        for resource in self.resources:
            tf_type = f"{resource.provider}_{resource.resource_type.value}"
            tf_block = f"""
resource "{tf_type}" "{resource.resource_id}" {{
  provider = "{resource.provider}"
  region   = "{resource.region}"

  # Configurações específicas do recurso
  {self._dict_to_hcl(resource.config)}

  # Tags de compliance para rastreabilidade
  tags = {{
    Compliance = "{','.join(resource.compliance_tags.keys())}"
    Deployment = "{self.stack_id}"
  }}
}}
"""
            tf_blocks.append(tf_block)

        return "\n".join(tf_blocks)

    def _dict_to_hcl(self, config: Dict) -> str:
        """Converte dicionário Python para sintaxe HCL (simplificado)."""
        lines = []
        for key, value in config.items():
            if isinstance(value, bool):
                lines.append(f"  {key} = {str(value).lower()}")
            elif isinstance(value, (int, float)):
                lines.append(f"  {key} = {value}")
            elif isinstance(value, str):
                lines.append(f'  {key} = "{value}"')
            elif isinstance(value, dict):
                lines.append(f"  {key} = {{")
                for k, v in value.items():
                    lines.append(f'    {k} = "{v}"')
                lines.append("  }")
            elif isinstance(value, list):
                lines.append(f'  {key} = {str(value).replace("'", '"')}')
        return "\n".join(lines)
