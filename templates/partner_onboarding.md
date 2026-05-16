# Template de Onboarding de Novo Parceiro (Arkhe OS - Substrato 207)

Bem-vindo à rede de Inteligência de Ameaças Federada (Federated Threat Intelligence) do Arkhe OS. Este documento serve como checklist para integração de sua organização.

## 1. Requisitos Técnicos
- [ ] Endpoint SIEM compatível com a API de ingestão de ameaças.
- [ ] Sistema de Ticketing (ServiceNow ou Jira) com API acessível.
- [ ] Capacidade de gerar e compartilhar um Hash de Chave API (API Key Hash).
- [ ] Adoção do framework de Privacidade Diferencial (DP).

## 2. Configuração de Privacidade (DP-ε)
Defina o seu epsilon (ε) de privacidade diferencial:
- **Alta Privacidade (ε < 0.5):** Maior ruído, menor precisão individual, alta proteção.
- **Média Privacidade (ε = 1.0):** Equilíbrio entre ruído e precisão.
- **Baixa Privacidade (ε > 2.0):** Menor ruído, alta precisão, menor proteção.

*Nota: O handshake de integração falhará se ε for menor que 0.1 ou maior que 5.0.*

## 3. Auto-Descoberta e Handshake
Submeta o payload JSON de sua organização para o endpoint de auto-descoberta (`discover_partner`), incluindo:
- `org_id`: Identificador único (ex: "ZAF-BANK-006")
- `name`: Nome da Instituição
- `org_type`: `bank`, `enterprise`, `government`, ou `telecom`
- `country`: Código do País (ex: "ZA")
- `siem_endpoint`: URL do SIEM
- `ticketing_system`: `servicenow` ou `jira`
- `ticketing_url`: URL da API do sistema de tickets
- `api_key_hash`: Hash SHA-256 da sua chave

Após a descoberta, inicie o `handshake_partner` com o seu `proposed_epsilon`.

## 4. Testes Iniciais
- [ ] Valide o Handshake.
- [ ] Envie um Threat Indicator de teste.
- [ ] Verifique se o ticket de teste foi criado no seu sistema.
