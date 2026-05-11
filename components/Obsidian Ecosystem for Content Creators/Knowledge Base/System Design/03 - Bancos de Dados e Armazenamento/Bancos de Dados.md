# 03 - Bancos de Dados e Armazenamento

A persistência é a base da memória do sistema (**Tzinor Memory State**).

## 🗄️ SQL vs NoSQL
- **SQL**: Estruturado, ACID (Ex: Transações no `x402Wallet`).
- **NoSQL**: Flexível, escalável (Ex: AkashaFS para armazenamento ontológico).

## 📐 Modelagem de Dados
Definir como os dados são organizados (Ex: Interfaces em `server/types.ts`).

## 🔍 Indexação
Otimiza a busca. Sem índices, a busca por ressonância semântica seria inviável.

## 🍰 Replicação e Sharding
- **Replicação**: Cópia de dados para tolerância a falhas.
- **Sharding**: Divisão de um banco de dados grande em partes menores (**shards**) distribuídas em diferentes nós.

---
[[Knowledge Base/System Design/Index|⬅️ Voltar ao Roadmap]]
