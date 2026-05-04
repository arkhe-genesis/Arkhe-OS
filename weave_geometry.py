#!/usr/bin/env python3
"""
TECE-GEOMETRIA (weave_geometry.py)
Unifica o Substrato 33 (Código Afim) com o Substrato 30 (Grafeno).
Usa a deformação do grafeno para ajustar as labels do lift CPM.
"""

import numpy as np
from graphene_resonator import GrapheneResonator

class MechanicallyProgrammableCode:
    def __init__(self, base_code_params, graphene_region):
        self.params = base_code_params
        self.graphene = graphene_region  # instância de GrapheneResonator
        self.shift_labels = np.zeros((192, 512), dtype=int)  # 1536 labels

    def calibrate_from_strain(self, strain_percent: float):
        """
        Ajusta as labels do lift CPM baseado na deformação local do grafeno.
        O PMF gerado pela deformação altera a fase dos acoplamentos.
        """
        self.graphene.strain = strain_percent
        pmf = self.graphene._calculate_pmf()  # Re-calcula PMF
        self.graphene.pmf = pmf

        # Mapeia o PMF para um deslocamento nas labels do CPM
        # 1 T de PMF -> shift de 1 posição no CPM
        delta_shift = int(pmf * 10)  # escala arbitrária para demonstração

        # Aplica o shift a todas as labels (simplificado)
        self.shift_labels = (self.shift_labels + delta_shift) % 32  # P=32

        return self.shift_labels

    def get_current_code_geometry(self) -> dict:
        """
        Retorna a geometria atual do código, que agora depende da deformação.
        """
        return {
            'strain': self.graphene.strain,
            'pmf_tesla': self.graphene.pmf,
            'shifts_applied': float(np.mean(self.shift_labels)),
            'code_parameters': self.params
        }

# Exemplo de uso
if __name__ == "__main__":
    graphene = GrapheneResonator(strain_percent=0.05)
    code_params = {'n': 16384, 'k': 4142, 'd': 40}
    mutable_code = MechanicallyProgrammableCode(code_params, graphene)

    print("Código sem deformação:", mutable_code.get_current_code_geometry())
    mutable_code.calibrate_from_strain(0.2)
    print("Código sob 0.2% de deformação:", mutable_code.get_current_code_geometry())
