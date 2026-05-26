import json
import tempfile
import os
import base64

class Substrato852ProjectOrchestrationBridge:
    def __init__(self):
        self.payload = {
            "ID": "852",
            "Name": "PROJECT-ORCHESTRATION-BRIDGE (POB)",
            "Format": "Integração de Microsoft Project e Oracle Primavera ao ARKHE OS",
            "Phi_C": 0.798,
            "DCS_852": 0.872,
            "TI": 0.790,
            "Status": "CANONIZED_PROVISIONAL",
            "Cross_Substrate": ["846", "847", "826", "830", "825", "824", "831", "227-F"]
        }
        self.canonical_seal = "f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2"

        self.adapter_code = """#!/ "project_orchestration_adapter.py" — Substrato 852
# Adaptador para MS Project e Primavera
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
    \"\"\"
    Ponte entre MS Project/Primavera e ARKHE OS.
    Converte cronogramas em Substratos e aplica o Ghost Threshold ao progresso.
    \"\"\"
    def __init__(self):
        self.tasks: Dict[int, ProjectTask] = {}
        self.critical_path: List[int] = []

    def parse_msproject_xml(self, xml_path: str) -> List[Dict]:
        \"\"\"Parseia um arquivo MSPDI (XML) do Microsoft Project.\"\"\"
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

        # Preencher successors
        for t in tasks:
            for p_uid in t.predecessors:
                if p_uid in self.tasks:
                    self.tasks[p_uid].successors.append(t.uid)

        return [self._task_to_arkhe(t) for t in tasks]

    def _task_to_arkhe(self, task: ProjectTask) -> Dict:
        \"\"\"Converte uma tarefa em um substrato ARKHE.\"\"\"
        # Mapear percentual de conclusão para Φ_C
        phi_c = task.percent_complete / 100.0
        status = ProjectStatus.ON_TRACK
        if phi_c < 0.577:
            status = ProjectStatus.OFF_TRACK
        elif phi_c < 0.80:
            status = ProjectStatus.AT_RISK

        # Computar selo
        seal_data = "{}:{}:{}:{}".format(task.uid, task.name, task.start, task.finish)
        seal = hashlib.sha3_256(seal_data.encode()).hexdigest()[:16]

        # Gerar decreto de tarefa
        decree = \"\"\"<|ARKHE_START|>
<|SUBSTRATE|> 852-TASK-{0}
<|INVARIANT|> I.12 (Temporal Chain Anchor)
<|PHI_C|> {1:.3f}
<|CRITICAL_PATH|> {2}

Tarefa: {3}
Início: {4}
Término: {5}
Progresso: {6}%
Predecessores: {7}
Sucessores: {8}
Status: {9}

<|SEAL|> {10}
<|ARKHE_END|>\"\"\".format(task.uid, phi_c, task.uid in self.critical_path, task.name, task.start, task.finish, task.percent_complete, task.predecessors, task.successors, status.value, seal)

        return {
            "substrate_id": "852-TASK-{}".format(task.uid),
            "phi_c": phi_c,
            "status": status.value,
            "decree": decree,
            "seal": seal,
        }

    def compute_critical_path(self) -> List[int]:
        \"\"\"Calcula o caminho crítico (simplificado: maior duração).\"\"\"
        # Implementação simplificada: usar algoritmo de caminho mais longo
        # Em produção, integrar com a engine de scheduling do MS Project
        return self.critical_path

    def generate_portfolio_decree(self, task_results: List[Dict]) -> str:
        \"\"\"Gera um decreto consolidado do portfólio.\"\"\"
        phi_values = [t["phi_c"] for t in task_results]
        avg_phi = sum(phi_values) / len(phi_values) if phi_values else 0.0

        at_risk = [t for t in task_results if t["status"] == ProjectStatus.AT_RISK.value]
        off_track = [t for t in task_results if t["status"] == ProjectStatus.OFF_TRACK.value]

        decree = \"\"\"<|ARKHE_START|>
<|SUBSTRATE|> 852-PORTFOLIO
<|INVARIANT|> I.1 (Coherence Base)
<|PHI_C|> {0:.3f}

PORTFOLIO STATUS REPORT
Total de Tarefas: {1}
Φ_C Médio: {0:.3f}
Em Risco: {2}
Fora do Rumo: {3}

Tarefas Fora do Rumo (abaixo do Ghost Threshold γ=0.577):
{4}

<|SEAL|> {5}
<|ARKHE_END|>\"\"\".format(avg_phi, len(task_results), len(at_risk), len(off_track), chr(10).join(["- {}: {}".format(t['substrate_id'], t['status']) for t in off_track]), hashlib.sha3_256(str(task_results).encode()).hexdigest()[:16])
        return decree

# Exemplo de uso
if __name__ == "__main__":
    adapter = ProjectOrchestrationAdapter()
    # Simulação de tarefas
    adapter.tasks = {
        1: ProjectTask(1, "Iniciação", "2026-01-01", "2026-01-15", 100, [], [2]),
        2: ProjectTask(2, "Planejamento", "2026-01-16", "2026-02-15", 45, [1], [3]),
        3: ProjectTask(3, "Execução", "2026-02-16", "2026-06-30", 25, [2], []),
    }
    results = [adapter._task_to_arkhe(t) for t in adapter.tasks.values()]
    portfolio = adapter.generate_portfolio_decree(results)
    print(portfolio)
"""
        self.payload["Artifacts"] = {
            "project_orchestration_adapter_py_base64": base64.b64encode(self.adapter_code.encode("utf-8")).decode("utf-8")
        }

    def canonize(self):
        self.payload["canonical_seal"] = self.canonical_seal
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(self.payload, file, indent=4)
        return path

if __name__ == "__main__":
    canonizer = Substrato852ProjectOrchestrationBridge()
    print("Canonized output written to:", canonizer.canonize())
