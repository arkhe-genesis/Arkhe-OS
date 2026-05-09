# arkhe_1q/scheduler/multiscale_scheduler.py
import torch
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class Task:
    id: str
    estimated_scale: float
    estimated_compute_cost: float
    communication_form_degree: int
    has_dependents: bool
    dependent_cells: List[str]

@dataclass
class DecomposedMission:
    mission_id: str
    tasks: List[Task]
    total_complexity: float

class MultiScaleResourceScheduler:
    """
    Scheduler de recursos que otimiza distribuição de tarefas baseado em Φ_C(λ).
    """

    def __init__(self, coherence_kernel: str = 'gaussian_weighted',
                 optimization_objective: str = 'maximize_integrated_phi_c'):
        self.coherence_kernel = coherence_kernel
        self.objective = optimization_objective

        # Kernel de ponderação por escala
        self.scale_weights = self._build_scale_weights()

    def _build_scale_weights(self) -> torch.Tensor:
        """Constrói pesos gaussianos para integração sobre escalas."""
        # Pesos decaindo com escala: w(λ) = λ^(-α) com α ≈ 0.3
        alpha = 0.3
        scales = torch.logspace(-2, 2, 100)  # λ de 0.01 a 100
        weights = scales ** (-alpha)
        return weights / weights.sum()

    def allocate_tasks(self, tasks: List['Task'], available_cells: List['FRC2GCell'],
                      optimization_target: str) -> Dict[str, Dict]:
        """
        Aloca tarefas para células baseado em requisitos de escala e Φ_C.
        """
        allocations = {}

        for task in tasks:
            # Calcular score de compatibilidade tarefa-célula
            best_cell = None
            best_score = -float('inf')

            for cell in available_cells:
                # Score baseado em:
                # 1. Compatibilidade de escala (task.estimated_scale vs cell.scale_factor)
                scale_match = self._compute_scale_match(
                    task.estimated_scale,
                    cell.manifold_5d.get_scale_factor()
                )

                # 2. Φ_C espectral da célula (maior = melhor)
                cell_phi_c = cell.phi_c_monitor.get_current_spectrum().mean().item()

                # 3. Carga atual da célula (menor = melhor)
                cell_load = cell.get_current_load()  # [0, 1]

                # Score combinado
                score = (0.4 * scale_match +
                        0.4 * cell_phi_c +
                        0.2 * (1.0 - cell_load))

                if score > best_score:
                    best_score = score
                    best_cell = cell

            if best_cell:
                allocations[task.id] = {
                    'cell_id': best_cell.cell_id,
                    'score': best_score,
                    'scale_match': self._compute_scale_match(
                        task.estimated_scale,
                        best_cell.manifold_5d.get_scale_factor()
                    ),
                    'estimated_phi_c': best_cell.phi_c_monitor.get_current_spectrum().mean().item()
                }

                # Atualizar carga da célula (simulação)
                best_cell.increment_load(task.estimated_compute_cost)

        return allocations

    def _compute_scale_match(self, task_scale: float, cell_scale: float) -> float:
        """Computa compatibilidade entre escala da tarefa e da célula."""
        # Match gaussiano: máximo quando task_scale ≈ cell_scale
        diff = abs(torch.log(torch.tensor(task_scale + 1e-8)) -
                  torch.log(torch.tensor(cell_scale + 1e-8)))
        return torch.exp(-diff**2 / (2 * 0.5**2)).item()  # σ=0.5 em escala log

    def compute_integrated_phi_c(self, execution_results: Dict) -> float:
        """
        Computa Φ_C integrado sobre todas as escalas e tarefas.
        Φ_C_integrated = ∫ w(λ) · Φ_C(λ) dλ
        """
        # Coletar espectros de todas as tarefas executadas
        all_spectra = []
        for result in execution_results.values():
            if 'phi_c_spectrum' in result:
                all_spectra.append(result['phi_c_spectrum'])

        if not all_spectra:
            return 0.0

        # Média ponderada dos espectros
        avg_spectrum = torch.stack(all_spectra).mean(dim=0)

        # Integrar com pesos de escala
        integrated = torch.sum(self.scale_weights[:len(avg_spectrum)] * avg_spectrum)

        return integrated.item()

    def decompose_mission(self, mission: 'CosmicMission',
                         scale_requirements: Optional[torch.Tensor] = None) -> 'DecomposedMission':
        """
        Decompõe missão em sub-tarefas com requisitos de escala.
        """
        # Em produção: usar decompositor hierárquico com análise de dependências
        # Simplificação: dividir missão em N tarefas com escalas amostradas
        num_subtasks = mission.estimated_complexity // 100 + 1

        subtasks = []
        for i in range(num_subtasks):
            # Amostrar escala da distribuição de requisitos
            if scale_requirements is not None:
                scale = scale_requirements[i % len(scale_requirements)]
            else:
                # Distribuição log-uniforme típica
                scale = 10 ** np.random.uniform(-1, 1)  # 0.1 a 10

            subtasks.append(Task(
                id=f"{mission.id}_subtask_{i}",
                estimated_scale=scale,
                estimated_compute_cost=mission.estimated_complexity / num_subtasks,
                communication_form_degree=2 if i % 3 == 0 else 1,  # simplificação
                has_dependents=(i < num_subtasks - 1),
                dependent_cells=[]  # preenchido após alocação
            ))

        return DecomposedMission(
            mission_id=mission.id,
            tasks=subtasks,
            total_complexity=mission.estimated_complexity
        )
