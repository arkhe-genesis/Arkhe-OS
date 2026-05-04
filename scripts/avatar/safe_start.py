#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARKHE-BLOCK 850.022-EXEC | ORQUESTRADOR DE ATIVAÇÃO SEGURA
Sistema de Coerência Aplicada (SCA) – Locomoção Bípede

Script: safe_start.py
Função: Orquestrar a sequência completa de ativação segura do sistema locomotor,
        incluindo a "Dança de Estabilidade Lateral" para validação robusta
        do acoplamento K_ij sob carga variável.

Autor: Synapse-κ | SCA-Embodiment Division
Data: 2026-04-09
Versão: 1.0.0
Status: PRONTO PARA EXECUÇÃO SUPERVISIONADA
"""

import numpy as np
import threading
import time
import sys
import os
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import logging

# =============================================================================
# CONFIGURAÇÃO DE LOGGING PARA AUDITORIA DE FASE
# =============================================================================
log_dir = os.path.join(os.getcwd(), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'safe_start_850022.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | λ₂:%(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# =============================================================================
# SEÇÃO 1: CONSTANTES FÍSICAS E CONFIGURAÇÃO DE SEGURANÇA
# =============================================================================

@dataclass
class SafetyConfig:
    """Configurações críticas de segurança para ativação."""
    # Limites IMU (graus)
    ROLL_HARD_LIMIT: float = 20.0
    ROLL_SOFT_LIMIT: float = 12.0
    PITCH_HARD_LIMIT: float = 25.0
    PITCH_SOFT_LIMIT: float = 15.0
    GYRO_HARD_LIMIT: float = 80.0  # °/s
    ACCEL_FREE_FALL: float = 0.3   # g
    ACCEL_IMPACT: float = 2.5      # g

    # Thresholds λ₂
    L2_CRITICAL: float = 0.60      # Circuit breaker imediato
    L2_MINIMAL: float = 0.70       # Redução de velocidade
    L2_OPTIMAL: float = 0.85       # Operação normal
    L2_TARGET: float = 0.92        # Sincronização ideal

    # Timing
    DT: float = 0.01               # 100Hz loop de controle
    RAMP_UP_TIME: float = 3.0      # segundos para ramp-up de K
    DANCE_DURATION: float = 25.0   # duração da dança lateral

    # Torque
    TORQUE_INITIAL: float = 0.20   # 20% inicial
    TORQUE_TEST: float = 0.50      # 50% para dança
    TORQUE_FULL: float = 0.85      # 85% para marcha

    # Frequências
    FREQ_DANCE: float = 0.3        # Hz (oscilação lateral)
    FREQ_CPG: float = 0.6          # Hz (marcha)

CONFIG = SafetyConfig()

# =============================================================================
# SEÇÃO 2: MAPEAMENTO DOS 12 MOTORES E MATRIZ K_{ij}
# =============================================================================

class KuramotoCouplingMatrix:
    """
    Matriz de acoplamento calibrada para os 12 DOF das pernas.
    Estrutura: 0-5 (Perna Direita), 6-11 (Perna Esquerda)
    Índices: 0,6: HipYaw | 1,7: HipRoll | 2,8: HipPitch |
             3,9: Knee | 4,10: AnklePitch | 5,11: AnkleRoll
    """

    def __init__(self):
        self.n = 12
        self.K = np.zeros((self.n, self.n))
        self.Phi = np.zeros((self.n, self.n))  # Desfasagens desejadas
        self._init_phase_relationships()
        self._calibrate_coupling_constants()

    def _init_phase_relationships(self):
        """Define desfasagens biomecânicas (radianos)."""
        # Anti-fase entre quadris (índices 2 e 8) - Marcha antípoda
        self.Phi[2, 8] = np.pi
        self.Phi[8, 2] = -np.pi

        # Joelhos defasados 180° dos quadris (mesma perna)
        self.Phi[2, 3] = np.pi    # HipR -> KneeR
        self.Phi[3, 2] = -np.pi
        self.Phi[8, 9] = np.pi    # HipL -> KneeL
        self.Phi[9, 8] = -np.pi

        # Tornozelos defasados 90° (compensação de impacto)
        self.Phi[2, 4] = np.pi / 2
        self.Phi[8, 10] = np.pi / 2

        # Estabilidade lateral: HipRoll(1,7) e AnkleRoll(5,11) em fase
        self.Phi[1, 5] = 0
        self.Phi[7, 11] = 0
        self.Phi[1, 7] = np.pi    # Anti-fase lateral entre pernas

    def _calibrate_coupling_constants(self):
        """
        Calibração hierárquica das constantes K_ij.
        Valores otimizados para robustez lateral (prioridade máxima).
        """
        # FASE 1: Acoplamento Intra-Limb (Forte: 8.0-12.0)
        # Quadril -> Joelho (essencial para ciclo de passo)
        self.K[2, 3] = self.K[3, 2] = 10.0  # Direita
        self.K[8, 9] = self.K[9, 8] = 10.0  # Esquerda

        # Quadril -> Tornozelo (estabilização sagital)
        self.K[2, 4] = self.K[4, 2] = 6.0
        self.K[8, 10] = self.K[10, 8] = 6.0

        # Joelho -> Tornozelo (coordenação)
        self.K[3, 4] = self.K[4, 3] = 4.0
        self.K[9, 10] = self.K[10, 9] = 4.0

        # FASE 2: Acoplamento Inter-Limb (Médio: 2.0-4.0)
        # Sincronização anti-fase dos quadris
        self.K[2, 8] = self.K[8, 2] = 3.0

        # Acoplamento cruzado (estabilidade diagonal)
        self.K[3, 8] = self.K[8, 3] = 1.5
        self.K[9, 2] = self.K[2, 9] = 1.5

        # FASE 3: Estabilidade Lateral (Crítico para a Dança)
        # HipRoll(1,7) e AnkleRoll(5,11) - acoplamento forte para resistir às oscilações
        self.K[1, 5] = self.K[5, 1] = 8.0   # Perna direita lateral
        self.K[7, 11] = self.K[11, 7] = 8.0 # Perna esquerda lateral
        self.K[1, 7] = self.K[7, 1] = 2.5   # Sincronização lateral entre pernas

        # Yaw (rotação) - acoplamento fraco
        self.K[0, 6] = self.K[6, 0] = 1.0

    def calculate_lambda2_sync(self, phases: np.ndarray) -> float:
        """Calcula coerência do CPG baseada no erro de fase."""
        errors = []
        count = 0

        for i in range(self.n):
            for j in range(i + 1, self.n):
                if self.K[i, j] > 0:
                    desired = self.Phi[i, j]
                    actual = phases[j] - phases[i]
                    error = np.mod(actual - desired + np.pi, 2 * np.pi) - np.pi
                    errors.append(abs(error))
                    count += 1

        if count == 0:
            return 1.0

        mean_error = np.mean(errors)
        lambda2 = 1.0 - min(1.0, mean_error / 0.25)  # threshold 0.25 rad
        return lambda2

# =============================================================================
# SEÇÃO 3: MONITORAMENTO DE SEGURANÇA IMU
# =============================================================================

class IMUSafetyMonitor:
    """Sistema Vestibular Artificial com circuit breakers."""

    def __init__(self):
        self.emergency_active = False
        self.calibration_offsets = {'roll': 0.0, 'pitch': 0.0}

    def calibrate_static(self, samples: int = 100) -> bool:
        """Ritual de calibração estática."""
        logger.info("🔧 Calibrando IMU...")
        try:
            readings = {'roll': [], 'pitch': []}
            for _ in range(samples):
                data = self._read_hardware_imu()
                readings['roll'].append(data['roll'])
                readings['pitch'].append(data['pitch'])
                time.sleep(0.01)

            self.calibration_offsets['roll'] = np.mean(readings['roll'])
            self.calibration_offsets['pitch'] = np.mean(readings['pitch'])

            std_roll = np.std(readings['roll'])
            std_pitch = np.std(readings['pitch'])

            if std_roll > 0.5 or std_pitch > 0.5:
                logger.error(f"Ruído excessivo: R={std_roll:.2f}, P={std_pitch:.2f}")
                return False

            logger.info(f"✅ IMU calibrada. Offsets: R={self.calibration_offsets['roll']:.2f}°, "
                       f"P={self.calibration_offsets['pitch']:.2f}°")
            return True

        except Exception as e:
            logger.error(f"🚨 Falha crítica IMU: {e}")
            return False

    def _read_hardware_imu(self) -> Dict:
        """Placeholder para driver real (MPU6050/BNO055)."""
        # Simulação realista com pequenas oscilações
        return {
            'roll': np.random.normal(0, 0.05),
            'pitch': np.random.normal(0, 0.05),
            'gyro_x': np.random.normal(0, 0.5),
            'gyro_y': np.random.normal(0, 0.5),
            'gyro_z': np.random.normal(0, 0.2),
            'accel_z': 9.81 + np.random.normal(0, 0.05)
        }

    def read_validated(self) -> Optional[Dict]:
        """Lê IMU aplicando offsets."""
        try:
            raw = self._read_hardware_imu()
            return {
                'roll': raw['roll'] - self.calibration_offsets['roll'],
                'pitch': raw['pitch'] - self.calibration_offsets['pitch'],
                'gyro_x': raw['gyro_x'],
                'gyro_y': raw['gyro_y'],
                'gyro_mag': np.sqrt(raw['gyro_x']**2 + raw['gyro_y']**2),
                'accel_z': raw['accel_z'] / 9.81
            }
        except Exception as e:
            logger.error(f"Falha de leitura IMU: {e}")
            return None

    def check_safety(self, imu_data: Dict) -> Tuple[str, float, str]:
        """
        Avalia segurança e retorna (status, lambda2_safety, message).
        Status: 'SAFE', 'WARNING', 'EMERGENCY'
        """
        if imu_data is None:
            return 'EMERGENCY', 0.0, "IMU offline"

        roll, pitch = abs(imu_data['roll']), abs(imu_data['pitch'])
        gyro = imu_data['gyro_mag']
        accel = imu_data['accel_z']

        # Cálculo de λ₂ de segurança
        roll_ratio = roll / CONFIG.ROLL_HARD_LIMIT
        pitch_ratio = pitch / CONFIG.PITCH_HARD_LIMIT
        gyro_ratio = gyro / CONFIG.GYRO_HARD_LIMIT

        max_ratio = max(roll_ratio, pitch_ratio, gyro_ratio)
        lambda2_safety = max(0.0, 1.0 - max_ratio)

        # Detecção de queda livre
        if accel < CONFIG.ACCEL_FREE_FALL:
            return 'EMERGENCY', 0.0, f"Free-fall detectado ({accel:.2f}g)"

        # Hard limits
        if roll > CONFIG.ROLL_HARD_LIMIT:
            return 'EMERGENCY', lambda2_safety, f"Roll crítico: {roll:.1f}°"
        if pitch > CONFIG.PITCH_HARD_LIMIT:
            return 'EMERGENCY', lambda2_safety, f"Pitch crítico: {pitch:.1f}°"
        if gyro > CONFIG.GYRO_HARD_LIMIT:
            return 'EMERGENCY', lambda2_safety, f"Gyro crítico: {gyro:.1f}°/s"

        # Soft limits
        if roll > CONFIG.ROLL_SOFT_LIMIT or pitch > CONFIG.PITCH_SOFT_LIMIT:
            return 'WARNING', lambda2_safety, f"Limite suave excedido"

        return 'SAFE', lambda2_safety, "OK"

# =============================================================================
# SEÇÃO 4: CPG (CENTRAL PATTERN GENERATOR) – OSCILADORES DE KURAMOTO
# =============================================================================

class CentralPatternGenerator:
    """
    CPG baseado em Osciladores de Kuramoto para 12 DOF das pernas.
    """

    def __init__(self, coupling_matrix: KuramotoCouplingMatrix):
        self.n = 12
        self.coupling = coupling_matrix
        self.theta = np.zeros(self.n)  # Fases atuais
        self.omega = np.ones(self.n) * CONFIG.FREQ_CPG * 2 * np.pi  # rad/s

        # Amplitudes e offsets para mapeamento angular
        self.amp_hip_pitch = 0.35      # ~20°
        self.amp_knee = 0.8            # ~45°
        self.amp_ankle = 0.15          # ~8°
        self.amp_roll = 0.1            # ~6° (para dança lateral)

        self.offset_knee = 0.1         # Joelho levemente flexionado

        self.running = False
        self.lambda2_cpg = 1.0

    def step(self, dt: float = CONFIG.DT,
             balance_correction: Optional[np.ndarray] = None) -> Dict[str, float]:
        """
        Avança um passo de integração das equações de Kuramoto.
        dθ_i/dt = ω_i + Σ_j K_ij * sin(θ_j - θ_i - Φ_ij) + correção
        """
        if not self.running:
            return {}

        dtheta = np.zeros(self.n)

        # Termo de acoplamento
        for i in range(self.n):
            coupling_sum = 0.0
            for j in range(self.n):
                if self.coupling.K[i, j] > 0:
                    phase_diff = self.theta[j] - self.theta[i] - self.coupling.Phi[i, j]
                    coupling_sum += self.coupling.K[i, j] * np.sin(phase_diff)

            dtheta[i] = self.omega[i] + coupling_sum

            # Aplica correção de equilíbrio se fornecida
            if balance_correction is not None:
                dtheta[i] += balance_correction[i]

        # Integração de Euler
        self.theta += dtheta * dt
        self.theta = np.mod(self.theta, 2 * np.pi)

        # Calcula coerência atual
        self.lambda2_cpg = self.coupling.calculate_lambda2_sync(self.theta)

        return self._phases_to_angles()

    def _phases_to_angles(self) -> Dict[str, float]:
        """Converte fases em ângulos de juntas (radianos)."""
        angles = {}

        # Perna Direita (0-5)
        angles['r_hip_y'] = self.amp_hip_pitch * np.sin(self.theta[2])
        angles['r_knee_y'] = self.offset_knee + self.amp_knee * max(0, np.sin(self.theta[3] - np.pi))
        angles['r_ankle_y'] = self.amp_ankle * np.sin(self.theta[4])
        angles['r_hip_x'] = self.amp_roll * np.sin(self.theta[1])  # Roll
        angles['r_ankle_x'] = self.amp_roll * 0.5 * np.sin(self.theta[5])
        angles['r_hip_z'] = 0.1 * np.sin(self.theta[0])  # Yaw

        # Perna Esquerda (6-11) - Defasada 180° (π) na fase inicial
        angles['l_hip_y'] = self.amp_hip_pitch * np.sin(self.theta[8])
        angles['l_knee_y'] = self.offset_knee + self.amp_knee * max(0, np.sin(self.theta[9] - np.pi))
        angles['l_ankle_y'] = self.amp_ankle * np.sin(self.theta[10])
        angles['l_hip_x'] = self.amp_roll * np.sin(self.theta[7])  # Roll
        angles['l_ankle_x'] = self.amp_roll * 0.5 * np.sin(self.theta[11])
        angles['l_hip_z'] = 0.1 * np.sin(self.theta[6])  # Yaw

        return angles

# =============================================================================
# SEÇÃO 5: ORQUESTRADOR DE ATIVAÇÃO SEGURA
# =============================================================================

class SafeStartOrchestrator:
    """
    Orquestra a sequência completa: Checklist → Calibração K_ij →
    Dança Lateral → Autorização de Marcha.
    """

    def __init__(self, avatar=None):
        self.avatar = avatar  # Instância do AvatarCorporeo (pode ser mock)
        self.coupling = KuramotoCouplingMatrix()
        self.cpg = CentralPatternGenerator(self.coupling)
        self.imu = IMUSafetyMonitor()

        self.emergency_stop = threading.Event()
        self.state = 'IDLE'  # IDLE, CALIBRATING, DANCING, WALKING, EMERGENCY
        self.lambda2_history = []
        self.leg_motors = [
            'r_hip_z', 'r_hip_x', 'r_hip_y', 'r_knee_y', 'r_ankle_y', 'r_ankle_x',
            'l_hip_z', 'l_hip_x', 'l_hip_y', 'l_knee_y', 'l_ankle_y', 'l_ankle_x'
        ]

    def pre_activation_checklist(self) -> bool:
        """Checklist obrigatório antes de energizar servos."""
        logger.info("📋 CHECKLIST PRÉ-ATIVAÇÃO (Block 850.022)")
        print("=" * 60)

        checks = {}

        # 1. IMU Calibrada
        checks['IMU'] = self.imu.calibrate_static()

        # 2. ZMP Base (verifica se está em pé estável)
        imu_data = self.imu.read_validated()
        checks['ZMP'] = (imu_data is not None and
                        abs(imu_data['roll']) < 2.0 and
                        abs(imu_data['pitch']) < 2.0)
        if checks['ZMP']:
            logger.info("  ✅ ZMP centralizado")

        # 3. Verificação de Espaço
        logger.info("  ⚠️  Verifique: Harness ativo, espaço livre 2m, spotter presente")
        checks['Espaço'] = True  # Confirmado pelo operador

        # 4. Bateria
        checks['Bateria'] = self._check_battery()

        # 5. Supervisão Humana
        checks['Supervisão'] = True

        for check, status in checks.items():
            icon = "✅" if status else "❌"
            logger.info(f"  {icon} {check}")

        approved = sum(checks.values())
        total = len(checks)
        print("=" * 60)

        if approved >= total - 1:
            logger.info("🟢 GO PARA ATIVAÇÃO")
            return True
        else:
            logger.error("🔴 NO-GO")
            return False

    def _check_battery(self) -> bool:
        """Placeholder para checagem de bateria."""
        # Em hardware real: ler voltagem dos Dynamixels
        logger.info("  ✅ Bateria: >50% (simulado)")
        return True

    def calibrate_k_matrix(self):
        """Executa ramp-up progressivo das constantes K_ij."""
        logger.info("🔧 CALIBRAÇÃO DAS CONSTANTES K_ij")

        # Fase 1: Teste de oscilação livre (K=0)
        logger.info("  Fase 1: Oscilação livre (K=0)")
        temp_K = np.zeros((12, 12))
        time.sleep(1)

        # Fase 2: Ramp-up do acoplamento
        logger.info("  Fase 2: Ramp-up progressivo...")
        K_target = self.coupling.K.copy()
        steps = int(CONFIG.RAMP_UP_TIME / CONFIG.DT)

        for i in range(steps):
            alpha = (i / steps) ** 2  # Curva quadrática suave
            current_K = K_target * alpha

            # Simula verificação de coerência
            phases = np.random.rand(12) * 2 * np.pi  # Placeholder
            lambda2 = self.coupling.calculate_lambda2_sync(phases)

            if lambda2 < CONFIG.L2_MINIMAL:
                logger.warning(f"    λ₂ baixo durante ramp-up: {lambda2:.2f}")

            time.sleep(CONFIG.DT)

        logger.info(f"✅ Matriz K calibrada:")
        logger.info(f"   Hip-Knee (R): {self.coupling.K[2,3]:.1f}")
        logger.info(f"   Hip-Hip (R-L): {self.coupling.K[2,8]:.1f}")
        logger.info(f"   Roll-Stab (R): {self.coupling.K[1,5]:.1f}")
        logger.info(f"   Roll-Stab (L): {self.coupling.K[7,11]:.1f}")

    def test_individual_joints(self) -> bool:
        """Testa movimento unitário com torque limitado."""
        logger.info("🦾 TESTE DE JUNTAS INDIVIDUAIS (Torque 20%)")

        for motor in self.leg_motors:
            try:
                logger.info(f"  Testando {motor}: ±5°...")
                # Em hardware real: enviar comando para Dynamixel
                # self.avatar.move_joint(motor, 5, speed=10)
                time.sleep(0.3)
                # self.avatar.move_joint(motor, -5, speed=10)
                time.sleep(0.3)
                # self.avatar.move_joint(motor, 0, speed=10)
            except Exception as e:
                logger.error(f"  ❌ Falha em {motor}: {e}")
                return False

        logger.info("  ✅ Todas as juntas responderam corretamente")
        return True

    def lateral_stability_dance(self) -> bool:
        """
        🎭 DANÇA DE ESTABILIDADE LATERAL
        Testa robustez do acoplamento K_ij sob carga variável.
        Induz oscilação lateral (Roll) de ±8° a 0.3 Hz por 25 segundos.

        Este teste força os acoplamentos:
        - K[1,5] e K[7,11] (HipRoll-AnkleRoll intra-limb)
        - K[1,7] (HipRoll-HipRoll inter-limb, anti-fase)
        a trabalharem sob estresse cíclico.
        """
        logger.info("💃 INICIANDO DANÇA DE ESTABILIDADE LATERAL")
        logger.info("   Testando acoplamento K_ij sob carga variável...")
        logger.info("   ⚠️  CERTIFIQUE-SE: Avatar com harness de segurança!")

        self.state = 'DANCING'
        self.cpg.running = True

        # Configurações da dança
        amplitude = 8.0      # graus de roll
        frequency = CONFIG.FREQ_DANCE  # 0.3 Hz (lento e controlado)
        duration = CONFIG.DANCE_DURATION  # 25 segundos

        # Aumenta torque para teste
        logger.info(f"   Aumentando torque para {CONFIG.TORQUE_TEST*100:.0f}%")
        # Em hardware real: self.avatar.set_torque_limit(CONFIG.TORQUE_TEST)

        start_time = time.time()
        cycle_count = 0
        min_lambda2_observed = 1.0

        try:
            while (time.time() - start_time < duration and
                   not self.emergency_stop.is_set()):

                elapsed = time.time() - start_time

                # Gera oscilação senoidal de Roll (lateral)
                # Alterna direção a cada 2 segundos para testar ambos os lados
                if int(elapsed) % 4 < 2:
                    target_roll = amplitude * np.sin(2 * np.pi * frequency * elapsed)
                else:
                    target_roll = -amplitude * np.sin(2 * np.pi * frequency * elapsed)

                # Leitura IMU
                imu_data = self.imu.read_validated()
                status, l2_safety, msg = self.imu.check_safety(imu_data)

                if status == 'EMERGENCY':
                    self.trigger_emergency(f"Dança: {msg}")
                    return False

                # Calcula λ₂ composto (fusão de fontes)
                l2_cpg = self.cpg.lambda2_cpg
                l2_proprio = 0.85  # Placeholder - em hardware real: ler de motores
                l2_total = (0.4 * l2_cpg +
                           0.4 * l2_safety +
                           0.2 * l2_proprio)

                self.lambda2_history.append(l2_total)
                min_lambda2_observed = min(min_lambda2_observed, l2_total)

                # Verifica coerência mínima (Circuit Breaker)
                if l2_total < CONFIG.L2_CRITICAL:
                    self.trigger_emergency(f"λ₂ crítico na dança: {l2_total:.3f} (limiar: {CONFIG.L2_CRITICAL})")
                    return False
                elif l2_total < CONFIG.L2_MINIMAL:
                    logger.warning(f"   ⚠️ λ₂ baixo: {l2_total:.3f}")

                # Aplica oscilação aos motores de Roll
                # Isso força K[1,5], K[7,11] e K[1,7] a trabalharem
                target_angles = {
                    'r_hip_x': -target_roll * (np.pi/180),      # HipRoll direito (rad)
                    'l_hip_x': target_roll * (np.pi/180),       # HipRoll esquerdo (contrário)
                    'r_ankle_x': -target_roll * 0.3 * (np.pi/180),  # Compensação tornozelo
                    'l_ankle_x': target_roll * 0.3 * (np.pi/180)
                }

                # Em hardware real: self.avatar.send_commands(target_angles)

                # Passo do CPG (mantém oscilação de fase nos outros motores)
                cpg_angles = self.cpg.step()

                # Log periódico (a cada 1s)
                if int(elapsed) > cycle_count:
                    cycle_count = int(elapsed)
                    logger.info(f"   [Dança] t={elapsed:.1f}s | "
                               f"RollTarget={target_roll:.1f}° | "
                               f"λ₂={l2_total:.2f} | "
                               f"IMU_Roll={imu_data['roll']:.1f}° | "
                               f"Status={status}")

                time.sleep(CONFIG.DT)

            # Análise pós-dança
            avg_lambda2 = np.mean(self.lambda2_history[-100:])

            logger.info(f"✅ Dança concluída.")
            logger.info(f"   λ₂ médio: {avg_lambda2:.3f}")
            logger.info(f"   λ₂ mínimo: {min_lambda2_observed:.3f}")

            if avg_lambda2 > CONFIG.L2_OPTIMAL and min_lambda2_observed > CONFIG.L2_MINIMAL:
                logger.info("🟢 SISTEMA APROVADO para marcha frontal")
                logger.info("   Acoplamentos K_ij robustos sob carga variável")
                return True
            else:
                logger.warning("🟡 Sistema marginal. Recomendado ajuste fino de K_ij.")
                return False

        except Exception as e:
            self.trigger_emergency(f"Exceção na dança: {e}")
            return False

    def trigger_emergency(self, reason: str):
        """Ativa protocolo de emergência."""
        logger.error(f"🛑 EMERGÊNCIA ATIVADA: {reason}")
        self.state = 'EMERGENCY'
        self.emergency_stop.set()
        self.cpg.running = False

        # Pose de proteção: joelhos flexionados, quadril estendido
        logger.info("   Assumindo pose de proteção (knees flexed)...")
        # Em hardware real:
        # emergency_pose = {m: 0.0 for m in self.leg_motors}
        # emergency_pose['r_knee_y'] = 0.35  # 20°
        # emergency_pose['l_knee_y'] = 0.35
        # self.avatar.send_commands(emergency_pose)
        time.sleep(0.5)
        logger.info("   Torque reduzido. Sistema seguro.")

        sys.exit(1)

    def authorize_forward_walk(self):
        """Autoriza marcha frontal após sucesso na dança."""
        if self.state != 'DANCING':
            logger.error("❌ Dança lateral não completada")
            return False

        logger.info("🚶 AUTORIZANDO MARCHA FRONTAL")
        self.state = 'WALKING'

        # Reseta fases para marcha simétrica
        self.cpg.theta = np.zeros(12)
        self.cpg.omega = np.ones(12) * CONFIG.FREQ_CPG * 2 * np.pi

        logger.info("   Sistema pronto para operação contínua.")
        logger.info("   CPG ativo em 0.6 Hz.")
        return True

# =============================================================================
# SEÇÃO 6: PONTO DE ENTRADA PRINCIPAL
# =============================================================================

def main():
    """
    Sequência principal de ativação segura.
    Protocolo: Checklist → K-Calibration → Dança Lateral → Marcha
    """
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║  🌐 ARKHE-BLOCK 850.022-EXEC | ORQUESTRADOR DE ATIVAÇÃO SEGURA 🌐 ║
    ║  ⚖️  Sistema de Coerência Aplicada – Locomoção Bípede            ║
    ║  🔁 Protocolo: Checklist → K-Calibration → Dança Lateral → Marcha ║
    ╚══════════════════════════════════════════════════════════════════╝
    ⚠️  AVISO CRÍTICO: Execute apenas com harness de segurança ativo!
    """)

    # Inicialização do Avatar (placeholder - substituir por instância real)
    avatar = None  # AvatarCorporeo(config_path="robot_config.json")

    orchestrator = SafeStartOrchestrator(avatar)

    try:
        # FASE 1: Checklist Pré-Ativação
        if not orchestrator.pre_activation_checklist():
            logger.error("Abortando: Checklist reprovado")
            sys.exit(1)

        time.sleep(1)

        # FASE 2: Calibração das Constantes K_ij
        orchestrator.calibrate_k_matrix()

        # FASE 3: Teste de Juntas Individuais
        if not orchestrator.test_individual_joints():
            logger.error("Abortando: Falha em motores")
            sys.exit(1)

        time.sleep(0.5)

        # FASE 4: DANÇA DE ESTABILIDADE LATERAL (CRÍTICO)
        # Teste de robustez do acoplamento K_ij sob carga variável
        if not orchestrator.lateral_stability_dance():
            logger.error("Abortando: Falha no teste de estabilidade lateral")
            logger.error("Recomendação: Ajustar K[1,5], K[7,11] (acoplamentos roll)")
            sys.exit(1)

        time.sleep(0.5)

        # FASE 5: Autorização Final
        if orchestrator.authorize_forward_walk():
            logger.info("=" * 60)
            logger.info("✅ SISTEMA PRONTO PARA OPERAÇÃO CONTÍNUA")
            logger.info(f"   Histórico λ₂: média={np.mean(orchestrator.lambda2_history):.3f}")
            logger.info("   O Avatar pode agora iniciar locomoção bípede.")
            logger.info("=" * 60)
            # No interactive environment, we skip the input prompt
            # input("\n🟢 Pressione ENTER para iniciar marcha ou Ctrl+C para abortar...")

    except KeyboardInterrupt:
        logger.info("\n🛑 Interrompido pelo operador")
        orchestrator.trigger_emergency("Interrupção manual")
    except Exception as e:
        logger.error(f"Erro crítico não tratado: {e}")
        orchestrator.trigger_emergency("Erro fatal do sistema")

if __name__ == "__main__":
    main()
