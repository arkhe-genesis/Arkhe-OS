#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/verify_qec_integration.py

import sys
import os
import numpy as np
import torch

from scripts.arkhe_qec_bridge import ArkheQECBridge

def verify():
    print("🜏 Iniciando Verificação de Integração QEC...")

    try:
        # 1. Initialize Bridge
        bridge = ArkheQECBridge(model_id=1, distance=7, n_rounds=7)
        print("[OK] Bridge QEC inicializada.")

        # 2. Simulate a non-trivial syndrome
        # For d=7, half = 24. For T=7, 2*T*half = 2*7*24 = 336
        half = (7*7 - 1) // 2
        T = 7
        syndrome = np.zeros((1, 2 * T * half), dtype=np.uint8)

        # Inject some errors in the syndrome
        syndrome[0, 10] = 1
        syndrome[0, 50] = 1
        syndrome[0, 100] = 1

        print(f"[INFO] Processando síndrome simulada (peso={np.sum(syndrome)})...")

        # 3. Process through Bridge
        result = bridge.process_syndrome(syndrome, basis="X")

        # 4. Validate output format
        pre_L = result['pre_L']
        residual = result['residual']

        print(f"[RESULT] Pre-L: {pre_L}")
        print(f"[RESULT] Residual shape: {residual.shape}")

        if residual.shape == (1, 336):
            print("[PASS] Formato do residual correto.")
        else:
            print(f"[FAIL] Formato do residual incorreto: {residual.shape}")
            return False

        # 5. Check if Pre-L is within expected values (0 or 1)
        if np.all((pre_L == 0) | (pre_L == 1)):
            print("[PASS] Valores de Pre-L válidos.")
        else:
            print(f"[FAIL] Valores de Pre-L inválidos: {pre_L}")
            return False

        print("🜏 Integração QEC Neural verificada com sucesso.")
        return True

    except Exception as e:
        print(f"[ERROR] Falha na verificação: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify()
    sys.exit(0 if success else 1)
