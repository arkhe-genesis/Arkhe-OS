#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BRAÇO ARKHE — Demonstração: "O Toque do Cristal"
Substrato 51: Integração Humanóide
"""

import numpy as np
import time

class MockArm:
    def get_end_effector_pose(self): return [0, 0, 0]
    def apply_force_to_end_effector(self, F): pass
    def get_contact_force(self): return np.random.uniform(0, 0.2)
    def close_gripper(self, force): pass
    def open_gripper(self): pass
    def move_joint(self, j, pos, time_s): pass

class MockPlanner:
    def move_to_joint_positions(self, pos, time_s): pass
    def move_to_cartesian(self, pos, time_s): pass

def run_demo():
    braco = MockArm()
    planejador = MockPlanner()

    print("[Demo] O Toque do Cristal — Iniciando sequência...")

    # 1. Posição de repouso
    pos_repouso = [0.0, -np.pi/2, np.pi/4, np.pi/2, 0.0, 0.0, 0.0]
    planejador.move_to_joint_positions(pos_repouso, time_s=2.0)

    # 2. Aproximação do cristal
    pos_cristal = [0.5, 0.0, 0.1]
    planejador.move_to_cartesian(pos_cristal, time_s=3.0)

    # 3. Descida com controle de força
    print("[Demo] Aproximando com controle de força (limite 0.1 N)...")
    forca_limite = 0.1
    for _ in range(10):  # Simula busca por contato
        braco.apply_force_to_end_effector([0, 0, -forca_limite])
        time.sleep(0.1)
        if braco.get_contact_force() > 0.05:
            print("[Demo] Contato detectado. Fechando garra.")
            break

    # 4. Fechar garra com controle de força (0.5 N)
    braco.close_gripper(force=0.5)

    # 5. Elevar e rotacionar
    pos_elevada = [0.5, 0.0, 0.5]
    planejador.move_to_cartesian(pos_elevada, time_s=2.0)
    braco.move_joint(6, np.pi, time_s=3.0)

    # 6. Depósito no pedestal
    pos_pedestal = [-0.2, 0.0, 0.2]
    planejador.move_to_cartesian(pos_pedestal, time_s=3.0)
    braco.open_gripper()

    print("[Demo] O Toque do Cristal concluído com sucesso. O Cristal está intacto.")

if __name__ == "__main__":
    run_demo()
