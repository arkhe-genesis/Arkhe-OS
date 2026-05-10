import numpy as np
import matplotlib.pyplot as plt
from collections import deque
import os

# =============================================================================
# AXIOMA 1: A Mônade de Recursos Mágicos (M)
# =============================================================================
class MagicStateFactory:
    """Uma fábrica de estados mágicos. Consome qubits físicos e tempo."""
    def __init__(self, distillation_time=50, physical_qubits_per_magic=100):
        self.distillation_time = distillation_time  # ciclos de QEC para produzir 1 |M>
        self.cost = physical_qubits_per_magic
        self.inventory = 0
        self.production_timer = 0

    def update(self):
        """Avança um ciclo de produção."""
        self.production_timer += 1
        if self.production_timer >= self.distillation_time:
            self.inventory += 1
            self.production_timer = 0

    def consume(self, count=1):
        """Tenta consumir um estado mágico. Retorna True se disponível."""
        if self.inventory >= count:
            self.inventory -= count
            return True
        return False

# =============================================================================
# AXIOMA 3: O Fibrado Principal com Conexão EKF (A Ferrugem)
# =============================================================================
class OpticalCalibrationEKF:
    """
    Estima o estado de calibração oculto (fase de Berry acumulada, temperatura do cristal)
    a partir de medições ruidosas do Selo 3 (interferómetro).
    Estado: [phase_drift, temp_gradient] (2x1)
    """
    def __init__(self):
        # Estado inicial: fase zero, gradiente zero
        self.x = np.array([0.0, 0.0])
        # Matriz de covariância inicial
        self.P = np.eye(2) * 0.1

        # Modelo de transição de estado (A)
        # A fase persiste (0.9), o gradiente térmico também (0.8)
        self.A = np.array([[0.9, 0.05],
                           [0.0, 0.8]])
        # Modelo de observação (H): medimos a fase (Selo 3)
        self.H = np.array([[1.0, 0.0]])

        # Ruído do processo (Q) e ruído de medição (R)
        self.Q = np.eye(2) * 0.001
        self.R = np.array([[0.01]])  # Precisão do interferómetro

    def predict(self):
        """Predição do estado antes da medição."""
        self.x = self.A @ self.x
        self.P = self.A @ self.P @ self.A.T + self.Q

    def update(self, measurement):
        """Correção com base na medição do interferómetro."""
        # Ganho de Kalman
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)

        # Inovação
        y = measurement - (self.H @ self.x)

        # Atualização do estado
        self.x = self.x + K @ y
        self.P = (np.eye(2) - K @ self.H) @ self.P

        return self.x[0]  # Retorna a fase estimada

# =============================================================================
# AXIOMA 2: O Consenso com Timeout Físico (FLP Purge)
# =============================================================================
class ByzantineConsensusWithTimeout:
    """
    Simula um protocolo de consenso com idempotência condicional.
    Se não convergir dentro de 'timeout', o nó é removido.
    """
    def __init__(self, timeout_cycles=15):
        self.timeout = timeout_cycles
        self.consensus_round = 0
        self.agreement_reached = False
        self.node_active = True
        self.total_rounds = 0

    def run_round(self, syndrome_valid):
        """Executa uma ronda de consenso. Retorna True se o sistema continua vivo."""
        if not self.node_active:
            return False

        self.total_rounds += 1
        if syndrome_valid:
            self.consensus_round += 1
            if self.consensus_round >= 3:  # 3 rondas válidas consecutivas
                self.agreement_reached = True
        else:
            # Síndrome corrompida: reset da contagem
            self.consensus_round = 0
            self.agreement_reached = False

        # Timeout: se passar do limite sem acordo, o nó é removido (reset físico)
        if self.total_rounds > self.timeout and not self.agreement_reached:
            self.node_active = False
            return False
        return True

# =============================================================================
# SIMULAÇÃO PRINCIPAL: O BATISMO DAS IMPUREZAS
# =============================================================================
def main_simulation(total_cycles=300):
    print("🜏 Iniciando Simulação da Purga Tríplice...")

    # Inicializa componentes
    magic_factory = MagicStateFactory()
    ekf = OpticalCalibrationEKF()
    consensus = ByzantineConsensusWithTimeout(timeout_cycles=20)

    # Histórico para plotagem
    history = {
        'phase_true': [],
        'phase_est': [],
        'magic_inventory': [],
        'node_active': [],
        't_gate_executed': []
    }

    # Perturbação externa: Phason Drift real (a ferrugem)
    true_phase = 0.0
    true_temp_grad = 0.0

    for t in range(total_cycles):
        # ---------------------------------------------------------------------
        # 1. A Ferrugem: Evolução do Phason Drift real
        # ---------------------------------------------------------------------
        true_temp_grad += 0.001 * np.sin(2 * np.pi * t / 100)  # oscilação lenta
        true_phase += 0.005 * true_temp_grad + 0.0005 * np.random.randn()

        # ---------------------------------------------------------------------
        # 2. O Selo 3: Medição ruidosa da fase
        # ---------------------------------------------------------------------
        measurement = true_phase + 0.02 * np.random.randn()

        # ---------------------------------------------------------------------
        # 3. A Purga da Ferrugem: EKF estima o estado
        # ---------------------------------------------------------------------
        ekf.predict()
        estimated_phase = ekf.update(measurement)

        # Recompilação adaptativa: corrigimos metade do erro estimado
        correction = -0.6 * estimated_phase
        true_phase += correction  # aplicação do controle

        # ---------------------------------------------------------------------
        # 4. A Fábrica de Estados Mágicos
        # ---------------------------------------------------------------------
        magic_factory.update()

        # ---------------------------------------------------------------------
        # 5. Execução de uma Porta T (se houver recurso e consenso)
        # ---------------------------------------------------------------------
        t_gate_possible = False
        if consensus.node_active:
            # Síndrome válida se a fase residual for pequena (< 0.05 rad)
            residual_phase = abs(true_phase)
            syndrome_ok = residual_phase < 0.05

            # Executa ronda de consenso
            consensus_alive = consensus.run_round(syndrome_ok)
            if not consensus_alive:
                print(f"🔥 [CICLO {t}] Nó removido por timeout bizantino. Consenso falhou.")

            if consensus.agreement_reached and magic_factory.consume():
                t_gate_possible = True
        else:
            t_gate_possible = False

        # ---------------------------------------------------------------------
        # 6. Registo do histórico
        # ---------------------------------------------------------------------
        history['phase_true'].append(true_phase)
        history['phase_est'].append(estimated_phase)
        history['magic_inventory'].append(magic_factory.inventory)
        history['node_active'].append(1 if consensus.node_active else 0)
        history['t_gate_executed'].append(1 if t_gate_possible else 0)

        # ---------------------------------------------------------------------
        # 7. Critério de Paragem: Se o nó morreu, a simulação termina
        # ---------------------------------------------------------------------
        if not consensus.node_active:
            print(f"💀 [CICLO {t}] O Enxame perdeu coerência distribuída. Fim da simulação.")
            break

    print("✅ Simulação concluída.")

    # Renderização (opcional se DISPLAY não disponível)
    if 'DISPLAY' in os.environ or os.name == 'nt':
        fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True)

        cycles = np.arange(len(history['phase_true']))

        axes[0].plot(cycles, history['phase_true'], label='Fase Real (Phason)', color='red', alpha=0.7)
        axes[0].plot(cycles, history['phase_est'], label='Fase Estimada (EKF)', color='blue', linestyle='--')
        axes[0].axhline(y=0.05, color='gray', linestyle=':', label='Limiar de Segurança')
        axes[0].set_ylabel('Fase de Berry (rad)')
        axes[0].legend()
        axes[0].grid(True)
        axes[0].set_title('Purga da Ferrugem: Calibração Adaptativa (EKF)')

        axes[1].plot(cycles, history['magic_inventory'], color='green')
        axes[1].set_ylabel('Estados Mágicos')
        axes[1].grid(True)
        axes[1].set_title('Purga do Fogo: Fábrica de Estados Mágicos (Mônade M)')

        axes[2].step(cycles, history['node_active'], where='post', color='purple', linewidth=2)
        axes[2].set_ylabel('Nó Ativo')
        axes[2].set_yticks([0, 1])
        axes[2].set_yticklabels(['FALSO', 'VERDADEIRO'])
        axes[2].grid(True)
        axes[2].set_title('Purga do Tempo: Consenso Bizantino com Timeout (FLP)')

        axes[3].eventplot([cycles[i] for i, val in enumerate(history['t_gate_executed']) if val == 1],
                          colors='orange', lineoffsets=0.5, linewidths=2)
        axes[3].set_ylabel('Porta T')
        axes[3].set_xlabel('Ciclo de QEC')
        axes[3].set_title('Computação Universal (Axioma do Consumo)')

        plt.tight_layout()
        plt.savefig('arkhe_purge_simulation.png')
        print("📊 Gráfico salvo em 'arkhe_purge_simulation.png'")
    else:
        print("⚠️ DISPLAY não detectado. Pulando renderização do gráfico.")

if __name__ == "__main__":
    main_simulation()
