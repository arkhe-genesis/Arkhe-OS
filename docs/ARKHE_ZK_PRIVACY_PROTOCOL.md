# Protocolo de Privacidade ZK Arkhe (Commit-and-Prove)

Este documento detalha a estratégia de **Auditoria Preservadora de Privacidade** implementada no sistema operacional ontológico Arkhe.

## 1. Visão Geral
O objetivo é permitir que analistas humanos identifiquem anomalias visuais na infraestrutura (via GLSL Ray Marching) e provem a existência de violações formais (SHACL) sem expor a URI do recurso afetado ou a estrutura interna da T-Box ao backend durante o processo de reporte.

## 2. Componentes Criptográficos
- **Circuitos R1CS (Circom 2.0):** Implementam a lógica de validação `sh:maxCount` e outros predicados SHACL.
- **Compromissos de Pedersen:** Utilizados para criar um `commitment` sobre a identidade do recurso ($URI$) de forma que o backend possa verificar se o recurso pertence à infraestrutura autorizada sem saber qual recurso é.
- **Protocolo Groth16 (Pinocchio):** Gera provas compactas ($O(1)$ em tamanho de prova e tempo de verificação) para validações complexas.

## 3. Fluxo de Trabalho (Commit-and-Prove)
1. **Identificação Visual:** O analista detecta uma anomalia visual (ex: perturbação de ruído em um nó).
2. **Desafio ZK:** O cliente solicita um desafio para o nó. O backend fornece parâmetros do circuito e limites de conformidade.
3. **Geração de Testemunha (WASM):** O cliente calcula localmente a contagem de propriedades do recurso e gera um compromisso $C = Pedersen(URI, salt)$.
4. **Geração de Prova:** O cliente gera uma prova ZK de que $Count(URI) > Limit$ AND $C$ é um compromisso válido.
5. **Reporte Cego:** O cliente envia a prova e o compromisso ao backend.
6. **Verificação no Backend:** O backend valida a prova e confirma que o compromisso $C$ está na whitelist de ativos, sem reverter a identidade do recurso.

## 4. Benefícios
- **Minimização de Superfície:** Atacantes não podem enumerar URIs interceptando o tráfego de auditoria.
- **Residência de Dados:** Informações sensíveis de configuração nunca deixam o nó de processamento local (browser do analista) em texto claro.
- **Integridade Garantida:** Provas matemáticas impossibilitam o forjamento de alertas por parte de clientes maliciosos.
