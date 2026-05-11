# SUBSTRATO 51: Protocolo de Atualização de Firmware Invariante

## 1. Objetivo
Permitir a evolução do software de controle (firmware) dos corpos Arkhe sem comprometer a integridade da calibração de hardware e a precisão invariante.

## 2. O Selo de Transição
Cada atualização de firmware é tratada como um evento de "Code Surgery" (Substrate 33).
1. **Checkpoint:** O estado atual (fase, força, métricas) é selado com quartzo.
2. **Deploy Dual:** O novo firmware roda em paralelo ao antigo em um manifold de sombra por 100 ciclos de controle (10 ms).
3. **Validação de Saída:** As forças calculadas pelo novo firmware devem ser idênticas às do antigo (erro < 1 nN) antes da comutação.

## 3. Invariância Binária
O firmware é compilado para ser "Hardware-Invariant". Ele não acessa registradores diretamente, mas utiliza uma camada de abstração geométrica que traduz vetores de força em padrões de fase de acordo com o modelo único de cada Músculo de Luz.

## 4. Rollback Automático
Se a métrica de invariância global cair abaixo de 0.9999 nos primeiros 60 segundos após a atualização, o sistema executa um rollback instantâneo para a versão selada no Checkpoint, garantindo a soberania física.
