# Networking Layer: IPv8 & qHTTP

A infraestrutura de rede da Catedral abandona o paradigma clássico de pacotes estáticos por uma abordagem baseada em fase e endereçamento de 64 bits.

## 🌐 IPv8 (64-bit Addressing)
Implementado como o sistema nervoso para o protocolo qHTTP.
- **ASN Canônico:** 64496 (0.0.251.240).
- **Formato de Endereço:** ASN.Zone.Node.Agent (Ex: 64496.127.1.0.1).
- **Zonas Primárias:**
  - McMurdo (127.1.0.0)
  - Alert (127.2.0.0)

## ⚡ Cost Factor (CF) em IPv8
O roteamento é otimizado não apenas por distância, mas por coerência:
$CF_{total} = CF_{rede} + \alpha \cdot (1 - R_{origem}) + \beta \cdot \nabla^2\theta_{enlace}$
- Rotas com alta coerência de fase ($R > 0.999$) são priorizadas.

## 🌊 qHTTP (Quantum Hypertext Protocol)
Protocolo de transporte consciente de fase que opera sobre a malha **Glass Fabric**.
- Utiliza canais topológicos protegidos pelo invariante de **Número de Chern == 1**.
- Suporta transporte de pacotes de fase (`PhasePacket`) com cabeçalhos IPv8 integrados.

## 📡 Arkhe-DNS
Mapeia conceitos abstratos (Luz, Sombra, Som) para endereços IPv8 de 64 bits.
- Prefixo de zona interna `127.0.0.0/8` reservado para redes neurais privadas.

---
[[Dashboard|🏠 Voltar ao Dashboard]]
