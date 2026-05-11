# Protocolo de Auditoria Cross-Jurisdição (Arkhe-CJ)

O protocolo Arkhe-CJ permite que autoridades regulatórias de múltiplas jurisdições (ex: ANPD no Brasil e EDPB na Europa) verifiquem a conformidade da Catedral Arkhe sem a necessidade de transferência de dados brutos entre fronteiras, preservando a soberania de dados e a privacidade dos cidadãos.

## 1. Funcionamento Técnico

1.  **Ancoragem Local:** Todos os dados permanecem na região de origem (ex: São Paulo para cidadãos brasileiros).
2.  **Geração de Prova (Audit Proof):** A Catedral gera um manifesto contendo metadados de conformidade, hashes de contexto e a âncora na Merkle Tree regional.
3.  **Verificação de Assinatura:** A prova é assinada digitalmente com a chave regional da Catedral.
4.  **Consenso Global:** O Merkle Root da transação é replicado globalmente, permitindo que qualquer autoridade verifique a existência e a integridade da decisão original sem ver o conteúdo sensível.

## 2. Metadados de Prova

Uma prova Arkhe-CJ contém:
- `decision_type`: Categoria da decisão.
- `context_hash`: Hash SHA-256 do contexto original (prova de integridade).
- `compliance_tags`: Artigos de lei vinculados.
- `merkle_root_anchor`: Posição imutável no ledger.

## 3. Benefícios

- **Zero-Data Transfer:** Cumpre restrições rigorosas de transferência internacional de dados.
- **Transparência Federada:** Reguladores podem "confiar verificando" via âncoras criptográficas.
- **Resiliência:** Mesmo em caso de isolamento regional, as provas globais permanecem verificáveis.
