# ARKHE OS: Partner Onboarding Checklist

Este documento define o processo padrão de integração para novos parceiros na malha federada do Sentinel Fabric. O objetivo é garantir conformidade de segurança, validação de privacidade diferencial e alinhamento com a Carta pela Soberania Digital.

## 1. Requisitos Pré-Integração
- [ ] O parceiro possui uma infraestrutura capaz de suportar contêineres Docker / Kubernetes.
- [ ] O parceiro concorda com os limites de ruído de privacidade diferencial ($\epsilon \in [2.0, 5.0]$).
- [ ] As chaves PQC (Post-Quantum Cryptography) foram geradas e a chave pública foi compartilhada com o consórcio.

## 2. Handshake Inicial (Auto-Descoberta)
- O parceiro deve iniciar o protocolo de handshake através da API de auto-descoberta (`/api/v1/discovery/handshake`).
- O payload deve conter:
  - `org_id`: Identificador exclusivo da organização.
  - `public_key`: Chave pública PQC.
  - `epsilon_policy`: Política de privacidade diferencial a ser utilizada.
- O Sentinel Fabric validará o payload e retornará um token de acesso temporário.

## 3. Configuração do Agente Local
- [ ] Implantar o `ProductionFederatedAggregator` no cluster local.
- [ ] Configurar conexão com o barramento Phi-Bus.
- [ ] Configurar conexão com a TemporalChain para ancoragem de eventos locais.
- [ ] (Opcional) Configurar integração com sistemas ITSM (ServiceNow/Jira) locais para recepção de alertas cross-org.

## 4. Validação de Envio (Staging)
- [ ] Enviar 10 relatórios simulados utilizando a chave de staging.
- [ ] Confirmar que o ruído de Laplace está sendo aplicado corretamente localmente (verificar métricas Prometheus).
- [ ] Confirmar que o Sentinel Fabric recebe e processa os relatórios no ambiente de staging.

## 5. Go-Live (Produção)
- [ ] Alternar configuração para o ambiente de produção.
- [ ] Realizar rotação das chaves PQC para as chaves reais de produção.
- [ ] O parceiro passa a fazer parte da malha federada de threat intelligence.