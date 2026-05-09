# 09 - Filas de Mensagens e Sistemas Assíncronos

Desacoplando o processamento para maior escalabilidade.

## 🎭 Arquitetura Orientada a Eventos
O sistema reage a mudanças de estado (Ex: `SimulationState` transmitido via SSE).

## 📥 Filas (Kafka, RabbitMQ)
Buffer para mensagens entre serviços. Na Catedral, as Deliberações são processadas de forma assíncrona.

## ⚙️ Background Processing
Processamento fora do fluxo principal da UI (Ex: `inference.worker.js`).

---
[[Knowledge Base/System Design/Index|⬅️ Voltar ao Roadmap]]
