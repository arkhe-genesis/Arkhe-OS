
# Arkhe(n) Infrastructure de Segurança (Defesa em Profundidade)

Este documento descreve a arquitetura de segurança estratificada da Arkhe, baseada no conceito de **Defesa em Profundidade** e **Zero Trust**, alinhada ao **NIST CSF 2.0**. A fundação desta arquitetura em nuvem é canonizada no [ANEXO FS-67: A Fortaleza de Cristal nas Nuvens](./ANEXO_FS67_CLOUD_SECURITY.md).

## 1. Identidade e Acesso (IAM) - O Novo Perímetro
- **Identidade Humana:** Provedor OIDC para autenticação JWT na Camada L7 (API Gateway).
- **Identidade de Carga de Trabalho:** SPIFFE/SPIRE para emissão de certificados mTLS de curta duração para microsserviços.

## 2. Segurança de Network (L3/L4)
- **Microssegmentação:** Implementação de `NetworkPolicies` no Kubernetes (Default Deny).
- **Service Mesh:** Autorização L7 baseada em atributos via Envoy/Istio.

## 3. Cadeia de Suprimentos e Compute (L5/L6)
- **Assinatura de Imagens:** Sigstore/Cosign para garantir a integridade do pipeline CI/CD.
- **Políticas de Admissão:** OPA/Gatekeeper para validar configurações de Pods em runtime.

## 4. Segurança de Dados e Privacidade (L7)
- **Criptografia:** Gestão de chaves via HashiCorp Vault / AWS KMS.
- **Data Masking:** Mascaramento de PII no Anti-Corruption Layer (ACL).

## 5. Detecção e Resposta (L7/L8)
- **Runtime Security:** Falco para monitorização de syscalls e deteção de anomalias no kernel.
- **SIEM:** Centralização de logs e alertas no Elastic Stack.

## 6. GRC Automatizada
- **Policy-as-Code:** Regras de negócio em Rego (OPA) integradas ao fluxo operacional.
- **Drift Detection:** Verificação contínua de desvios entre IaC (Git) e o estado real.

## Integração no Pipeline CI/CD (Shift-Left Security)

```yaml
name: Secure CI/CD Pipeline
on:
  push:
    branches: [main]

jobs:
  sast-sca:
    steps:
      - name: Static Code Analysis (SAST)
        uses: github/semgrep@v1
      - name: Software Composition Analysis (SCA)
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'

  container-security:
    needs: sast-sca
    steps:
      - name: Build Image
        run: docker build -t myapp:${{ github.sha }} .
      - name: Scan Image for Vulnerabilities
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: "myapp:${{ github.sha }}"
          severity: 'CRITICAL,HIGH'
          exit-code: '1'
      - name: Sign Image with Cosign
        run: |
          cosign sign --key env://COSIGN_PRIVATE_KEY myapp:${{ github.sha }}
```

## Arquitetura de Referência

```text
[Usuário / Sistema Externo]
         |
         v
+-------------------------------------------------------------------+
| API Gateway (Traefik / Envoy)                                      |
| - Validação JWT / mTLS (L7)                                         |
+-------------------------------------------------------------------+
         |
         v
+-------------------------------------------------------------------+
| Kubernetes Cluster                                                |
| +-------------------+  +-------------------+  +-------------------+ |
| | Service Mesh     |  | Admission Ctrl   |  | Runtime Security | |
| | (Istio mTLS/L7)  |->| (OPA/Gatekeeper) |->| (Falco Syscalls) | |
| +-------------------+  +-------------------+  +-------------------+ |
+-------------------------------------------------------------------+
```
