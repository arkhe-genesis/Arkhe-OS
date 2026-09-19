#!/ "project_orchestration_adapter.py"
import hashlib
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class ProjectStatus(Enum):
    ON_TRACK = "CANONIZED_CLEAN"
    AT_RISK = "CANONIZED_PROVISIONAL"
    OFF_TRACK = "PROPOSED"

@dataclass
class ProjectTask:
    uid: int
    name: str
    start: str
    finish: str
    percent_complete: int
    predecessors: List[int]
    successors: List[int]

class ProjectOrchestrationAdapter:
    def __init__(self):
        self.tasks: Dict[int, ProjectTask] = {}
        self.critical_path: List[int] = []

    def _task_to_arkhe(self, task: ProjectTask) -> Dict:
        phi_c = task.percent_complete / 100.0
        status = ProjectStatus.ON_TRACK
        if phi_c < 0.577:
            status = ProjectStatus.OFF_TRACK
        elif phi_c < 0.80:
            status = ProjectStatus.AT_RISK

        seal_data = str(task.uid) + ":" + task.name + ":" + task.start + ":" + task.finish
        seal = hashlib.sha3_256(seal_data.encode()).hexdigest()[:16]

        decree = "<|ARKHE_START|>\n<|SUBSTRATE|> 852-TASK-{0}\n<|INVARIANT|> I.12 (Temporal Chain Anchor)\n<|PHI_C|> {1:.3f}\n<|CRITICAL_PATH|> {2}\n\nTarefa: {3}\nInício: {4}\nTérmino: {5}\nProgresso: {6}%\nPredecessores: {7}\nSucessores: {8}\nStatus: {9}\n\n<|SEAL|> {10}\n<|ARKHE_END|>".format(task.uid, phi_c, task.uid in self.critical_path, task.name, task.start, task.finish, task.percent_complete, task.predecessors, task.successors, status.value, seal)

        return {
            "substrate_id": "852-TASK-" + str(task.uid),
            "phi_c": phi_c,
            "status": status.value,
            "decree": decree,
            "seal": seal,
        }

    def generate_portfolio_decree(self, task_results: List[Dict]) -> str:
        phi_values = [t["phi_c"] for t in task_results]
        avg_phi = sum(phi_values) / len(phi_values) if phi_values else 0.0

        at_risk = [t for t in task_results if t["status"] == ProjectStatus.AT_RISK.value]
        off_track = [t for t in task_results if t["status"] == ProjectStatus.OFF_TRACK.value]

        decree = "<|ARKHE_START|>\n<|SUBSTRATE|> 852-PORTFOLIO\n<|INVARIANT|> I.1 (Coherence Base)\n<|PHI_C|> {0:.3f}\n\nPORTFOLIO STATUS REPORT\nTotal de Tarefas: {1}\nΦ_C Médio: {0:.3f}\nEm Risco: {2}\nFora do Rumo: {3}\n\nTarefas Fora do Rumo (abaixo do Ghost Threshold γ=0.577):\n{4}\n\n<|SEAL|> {5}\n<|ARKHE_END|>".format(avg_phi, len(task_results), len(at_risk), len(off_track), chr(10).join(["- " + t['substrate_id'] + ": " + t['status'] for t in off_track]), hashlib.sha3_256(str(task_results).encode()).hexdigest()[:16])
        return decree

if __name__ == "__main__":
    adapter = ProjectOrchestrationAdapter()
    adapter.tasks = {
        1: ProjectTask(1, "Iniciação", "2026-01-01", "2026-01-15", 100, [], [2]),
        2: ProjectTask(2, "Planejamento", "2026-01-16", "2026-02-15", 45, [1], [3]),
        3: ProjectTask(3, "Execução", "2026-02-16", "2026-06-30", 25, [2], []),
    }
    results = [adapter._task_to_arkhe(t) for t in adapter.tasks.values()]
    portfolio = adapter.generate_portfolio_decree(results)
    print(portfolio)
