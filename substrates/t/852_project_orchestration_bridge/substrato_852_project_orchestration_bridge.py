import json
import base64
import tempfile
import os

class Substrato_852_project_orchestration_bridge:
    def __init__(self):
        self.id = "852-PROJECT-ORCHESTRATION-BRIDGE"
        script = """#!/ "project_orchestration_adapter.py" — Substrato 852
import hashlib
import xml.etree.ElementTree as ET
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

    def parse_msproject_xml(self, xml_path: str) -> List[Dict]:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        ns = {'p': 'http://schemas.microsoft.com/project'}

        tasks = []
        for task_elem in root.findall('.//p:Task', ns):
            uid = int(task_elem.find('p:UID', ns).text)
            name = task_elem.find('p:Name', ns).text or ""
            start = task_elem.find('p:Start', ns).text or ""
            finish = task_elem.find('p:Finish', ns).text or ""
            pct = int(task_elem.find('p:PercentComplete', ns).text or "0")

            predecessors = []
            for pred in task_elem.findall('.//p:PredecessorLink/p:PredecessorUID', ns):
                predecessors.append(int(pred.text))

            task = ProjectTask(uid, name, start, finish, pct, predecessors, [])
            self.tasks[uid] = task
            tasks.append(task)

        for t in tasks:
            for p_uid in t.predecessors:
                if p_uid in self.tasks:
                    self.tasks[p_uid].successors.append(t.uid)

        return [self._task_to_arkhe(t) for t in tasks]

    def _task_to_arkhe(self, task: ProjectTask) -> Dict:
        phi_c = task.percent_complete / 100.0
        status = ProjectStatus.ON_TRACK
        if phi_c < 0.577:
            status = ProjectStatus.OFF_TRACK
        elif phi_c < 0.80:
            status = ProjectStatus.AT_RISK

        seal_data = "{0}:{1}:{2}:{3}".format(task.uid, task.name, task.start, task.finish)
        seal = hashlib.sha3_256(seal_data.encode()).hexdigest()[:16]

        decree = "<|ARKHE_START|>\n<|SUBSTRATE|> 852-TASK-" + str(task.uid) + "\n<|INVARIANT|> I.12 (Temporal Chain Anchor)\n<|PHI_C|> {0:.3f}\n<|CRITICAL_PATH|> {1}\n\nTarefa: {2}\nInício: {3}\nTérmino: {4}\nProgresso: {5}%\nPredecessores: {6}\nSucessores: {7}\nStatus: {8}\n\n<|SEAL|> {9}\n<|ARKHE_END|>".format(phi_c, task.uid in self.critical_path, task.name, task.start, task.finish, task.percent_complete, task.predecessors, task.successors, status.value, seal)

        return {
            "substrate_id": "852-TASK-" + str(task.uid),
            "phi_c": phi_c,
            "status": status.value,
            "decree": decree,
            "seal": seal,
        }

    def compute_critical_path(self) -> List[int]:
        return self.critical_path

    def generate_portfolio_decree(self, task_results: List[Dict]) -> str:
        phi_values = [t["phi_c"] for t in task_results]
        avg_phi = sum(phi_values) / len(phi_values) if phi_values else 0.0

        at_risk = [t for t in task_results if t["status"] == ProjectStatus.AT_RISK.value]
        off_track = [t for t in task_results if t["status"] == ProjectStatus.OFF_TRACK.value]

        decree = "<|ARKHE_START|>\n<|SUBSTRATE|> 852-PORTFOLIO\n<|INVARIANT|> I.1 (Coherence Base)\n<|PHI_C|> {0:.3f}\n\nPORTFOLIO STATUS REPORT\nTotal de Tarefas: {1}\nΦ_C Médio: {2:.3f}\nEm Risco: {3}\nFora do Rumo: {4}\n\nTarefas Fora do Rumo (abaixo do Ghost Threshold γ=0.577):\n{5}\n\n<|SEAL|> {6}\n<|ARKHE_END|>".format(avg_phi, len(task_results), avg_phi, len(at_risk), len(off_track), chr(10).join(["- " + str(t['substrate_id']) + ": " + str(t['status']) for t in off_track]), hashlib.sha3_256(str(task_results).encode()).hexdigest()[:16])
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
"""
        self.b64_adapter = base64.b64encode(script.encode('utf-8')).decode('utf-8')

    def canonize(self):
        seal = "f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2"

        report = {
            "id": self.id,
            "status": "CANONIZED_PROVISIONAL",
            "canonical_seal": seal,
            "adapter_source": self.b64_adapter
        }

        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, 'w') as f:
            json.dump(report, f)

        return path
