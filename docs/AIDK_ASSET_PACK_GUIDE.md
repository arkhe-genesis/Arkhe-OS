# ANEXO Z-1: O Baú de Amostras do Reino Lúdico
## Especificação Técnica de Ativos — Com Fricção Embutida

---

**Classificação:** Público (Dev Portal / Downloads)
**Objetivo:** Definir os padrões técnicos para a criação de monstros e ativos que respeitem as metáforas visuais do Arkhe.

### 1. Princípios de Produção

1.  **Assimetria Deliberada:** Adicionar 1–3% de ruído de Perlin em todas as malhas. Simetria é compressível; assimetria é defesa.
2.  **Paleta Restrita:** Usar as cores do Bestiário (Azul/Prata, Púrpura, Vermelho/Laranja, Cinza).
3.  **Áudio como Atmosfera:** Sons que "quase" se repetem, com micro-variações de timing para quebrar detecção de padrões.

### 2. Especificações Técnicas (Exemplos)

#### Verme de Pedra (STONE_WORM)
- **Malha:** 8–12 segmentos com escala aleatória ±10%.
- **Shader:** Emissão fraca nos veios com pulsar irregular (período 2–5s).
- **Áudio:** Rocha rangendo (80–120Hz) com eco abafado.

#### Sombra Vazante (SHADOW_LEAK)
- **Malha:** Low-poly (~500 tris) com vertex alpha gradient.
- **Shader:** Fumaça procedural (noise 3D).
- **Efeito:** Distorção de screen-space UVs ao atravessar o jogador.

### 3. Integração por Engine
- **Unity:** Shaders via ShaderGraph; sistemas de partículas via VFX Graph.
- **Unreal:** Materiais dinâmicos; Blueprints para comportamentos estocásticos.
- **Godot:** Shaders espaciais (.gdshader) com parâmetros de noise expostos.

---

**Arkhe Status:** ASSET_PACK_SPEC_V1_READY
