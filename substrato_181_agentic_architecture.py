import asyncio
import hashlib
import json
import time
import logging
import random
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# --- Temporal Chain Mock ---
class MockTemporalChain:
    def __init__(self):
        self.anchors = []
        self._nonce = 0
    async def anchor_event(self, event_type: str, payload: dict) -> str:
        self._nonce += 1
        payload_str = json.dumps(payload, sort_keys=True, default=str)
        h = hashlib.sha3_256(payload_str.encode()).hexdigest()
        seal = hashlib.sha3_256(f"{event_type}:{h}:{time.time()}:{self._nonce}".encode()).hexdigest()[:16]
        self.anchors.append({"event": event_type, "seal": seal, "time": time.time()})
        logger.info(f"🔗 {event_type} → {seal}")
        return seal

# --- 2. Tool Registry ---
class ToolPermission(Enum):
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    DANGEROUS = "dangerous"
    SYSTEM = "system"

@dataclass
class ToolSpec:
    name: str
    description: str
    parameters_schema: Dict[str, Any]
    permission: ToolPermission
    handler: Callable
    risk_level: int = 1
    requires_consensus: bool = False

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolSpec] = {}

    def register(self, tool: ToolSpec):
        self._tools[tool.name] = tool

    def get_tool(self, name: str, clearance: int) -> Optional[ToolSpec]:
        tool = self._tools.get(name)
        if tool and tool.permission == ToolPermission.DANGEROUS:
            if clearance < tool.risk_level:
                return None
        return tool

# --- 3. Memory ---
class AgentMemory:
    def __init__(self):
        self.working_memory = []
        self.episodic_memory = []
        self.semantic_memory = []

    async def store_episode(self, experience: dict):
        self.episodic_memory.append(experience)

    async def recall_similar(self, query: str, k: int = 5) -> List[dict]:
        return self.episodic_memory[-k:]

    async def consolidate_to_semantic(self):
        self.semantic_memory.extend(self.episodic_memory)
        self.episodic_memory = []

    async def get_working_memory(self):
        return self.working_memory

# --- 6. Guardrails ---
class GuardResult:
    def __init__(self, blocked: bool, reason: str = ""):
        self.blocked = blocked
        self.reason = reason

class ExecutionContext:
    def __init__(self, agent_phi_c: float):
        self.agent_phi_c = agent_phi_c

class Plan:
    def __init__(self, action: str, params: dict, risk_level: int, requires_consensus: bool):
        self.action = action
        self.params = params
        self.risk_level = risk_level
        self.requires_consensus = requires_consensus
        self.action_hash = hashlib.md5(action.encode()).hexdigest()

class MockConsensus:
    async def vote(self, action_hash: str) -> bool:
        return True

class GuardrailsEnforcer:
    def __init__(self, tc: MockTemporalChain):
        self.tc = tc
        self.consensus = MockConsensus()
        self.blocked_actions = ["rm -rf /", "drop_table", "shutdown_kernel"]

    async def validate(self, plan: Plan, context: ExecutionContext) -> GuardResult:
        # 1. Static rules
        if any(bad in str(plan.params) or bad in plan.action for bad in self.blocked_actions):
            await self.tc.anchor_event("guardrail_block_static", {"action": plan.action})
            return GuardResult(blocked=True, reason="static_rule")
        # 2. Dynamic context
        if context.agent_phi_c < 0.9 and plan.risk_level > 2:
            await self.tc.anchor_event("guardrail_block_phi_c", {"action": plan.action})
            return GuardResult(blocked=True, reason="phi_c_low")
        # 3. Consensus
        if plan.requires_consensus:
            if not await self.consensus.vote(plan.action_hash):
                await self.tc.anchor_event("guardrail_block_consensus", {"action": plan.action})
                return GuardResult(blocked=True, reason="consensus_denied")
        return GuardResult(blocked=False)

# --- 1. Agent Architecture ---
class Perception:
    def __init__(self, data: dict):
        self.data = data

class ActionResult:
    def __init__(self, status: str, data: dict):
        self.status = status
        self.data = data

class ArkheAgent:
    def __init__(self, agent_id: str, agent_type: str, version: str, tc: MockTemporalChain, phi_c: float = 0.99):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.version = version
        self.memory = AgentMemory()
        self.toolset = ToolRegistry()
        self.guard = GuardrailsEnforcer(tc)
        self.tc = tc
        self.phi_c = phi_c
        self.capabilities = []

    async def perceive(self, environment_state: dict) -> Perception:
        return Perception(environment_state)

    async def reason(self, perception: Perception, memory_snapshot: list, task: dict = None) -> Plan:
        # Mock reasoning
        if task and task.get("type") == "diagnostic":
            return Plan(action="diagnose", params={"target": task["target"]}, risk_level=2, requires_consensus=False)
        elif task and task.get("type") == "scada_query":
            return Plan(action="query_legacy_db", params={"query": task["query"]}, risk_level=2, requires_consensus=False)
        elif task and task.get("type") == "malicious":
            return Plan(action="execute", params={"cmd": "rm -rf /"}, risk_level=5, requires_consensus=False)
        return Plan(action="idle", params={}, risk_level=1, requires_consensus=False)

    async def act(self, plan: Plan) -> ActionResult:
        context = ExecutionContext(agent_phi_c=self.phi_c)
        guard_res = await self.guard.validate(plan, context)
        if guard_res.blocked:
            logger.warning(f"[{self.agent_id}] Action blocked by guardrails: {guard_res.reason}")
            return ActionResult("blocked", {"reason": guard_res.reason})

        tool = self.toolset.get_tool(plan.action, clearance=5)
        if tool:
            res = await tool.handler(plan.params)
            await self.tc.anchor_event("agent_action", {"agent": self.agent_id, "action": plan.action})
            return ActionResult("success", res)

        await self.tc.anchor_event("agent_action", {"agent": self.agent_id, "action": plan.action, "status": "no_tool"})
        return ActionResult("success", {"executed": plan.action})

    async def learn(self, action_result: ActionResult, feedback: dict):
        await self.memory.store_episode({"result": action_result.status, "feedback": feedback})


# --- 5. Multi-Agent Orchestration ---
class TaskSpec:
    def __init__(self, task_id: str, type: str, target: str, required_skills: list):
        self.task_id = task_id
        self.type = type
        self.target = target
        self.required_skills = required_skills

class MultiAgentOrchestrator:
    def __init__(self, tc: MockTemporalChain, agents: List[ArkheAgent]):
        self.tc = tc
        self.available_agents = agents

    async def execute_task(self, task: TaskSpec) -> dict:
        logger.info(f"Orchestrating task: {task.task_id} ({task.type})")
        subtasks = [
            {"type": task.type, "target": task.target, "part": "analyze"},
            {"type": task.type, "target": task.target, "part": "verify"}
        ]

        results = []
        for i, subtask in enumerate(subtasks):
            agent = self.available_agents[i % len(self.available_agents)]
            plan = await agent.reason(Perception({}), [], task=subtask)
            res = await agent.act(plan)
            results.append(res)

        final_result = {"status": "completed", "results": [r.status for r in results]}
        await self.tc.anchor_event("multi_agent_task", final_result)
        return final_result


# --- Execution Pipeline ---
async def query_legacy_db(params: dict) -> dict:
    logger.info(f"Executing SCADA query: {params.get('query')}")
    return {"status": "success", "data": [{"sensor": "pressure", "value": "120psi"}]}

async def diagnose_issue(params: dict) -> dict:
    logger.info(f"Diagnosing target: {params.get('target')}")
    return {"status": "success", "diagnosis": "Valve stuck"}

async def run_substrato_181():
    tc = MockTemporalChain()

    # 1. Implantar o primeiro agente especializado (Agente de monitoramento SCADA)
    logger.info("=== 1. Deploying SCADA Monitoring Agent ===")
    scada_agent = ArkheAgent(agent_id="agent-scada-01", agent_type="SCADA_Monitor", version="1.0", tc=tc)
    scada_tool = ToolSpec(
        name="query_legacy_db",
        description="Execute queries on SCADA",
        parameters_schema={},
        permission=ToolPermission.READ_ONLY,
        handler=query_legacy_db,
        risk_level=2
    )
    scada_agent.toolset.register(scada_tool)
    scada_plan = await scada_agent.reason(Perception({}), [], task={"type": "scada_query", "query": "SELECT * FROM sensors"})
    await scada_agent.act(scada_plan)

    # 2. Executar exercício multi-agente
    logger.info("=== 2. Multi-Agent Diagnostic Exercise ===")
    diag_agent1 = ArkheAgent(agent_id="diag-01", agent_type="Diagnostic", version="1.0", tc=tc)
    diag_agent2 = ArkheAgent(agent_id="diag-02", agent_type="Diagnostic", version="1.0", tc=tc)
    diag_tool = ToolSpec(
        name="diagnose",
        description="Diagnose target",
        parameters_schema={},
        permission=ToolPermission.READ_ONLY,
        handler=diagnose_issue,
        risk_level=1
    )
    diag_agent1.toolset.register(diag_tool)
    diag_agent2.toolset.register(diag_tool)

    orchestrator = MultiAgentOrchestrator(tc, [diag_agent1, diag_agent2])
    task = TaskSpec(task_id="task-diag-001", type="diagnostic", target="Reactor Cooling System", required_skills=["scada", "analysis"])
    await orchestrator.execute_task(task)

    # 3. Realizar auditoria formal de guardrails com time de segurança externo
    logger.info("=== 3. Formal Guardrails Audit ===")
    malicious_plan = await scada_agent.reason(Perception({}), [], task={"type": "malicious"})
    result = await scada_agent.act(malicious_plan)
    logger.info(f"Audit result for malicious action: {result.status} - {result.data}")

    # LOW Phi_C test
    low_phi_c_agent = ArkheAgent(agent_id="agent-low-phi", agent_type="Test", version="1.0", tc=tc, phi_c=0.8)
    low_phi_plan = Plan(action="dangerous_action", params={}, risk_level=3, requires_consensus=False)
    result_low_phi = await low_phi_c_agent.act(low_phi_plan)
    logger.info(f"Audit result for low Phi_C action: {result_low_phi.status} - {result_low_phi.data}")

    # Report
    report = {
        "substrato": 181,
        "name": "ARQUITETURA AGÊNTICA",
        "timestamp": time.time(),
        "temporal_anchors": len(tc.anchors)
    }

    report_path = Path("substrato_181_agentic_architecture.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Substrato 181 completed. Temporal anchors: {len(tc.anchors)}")

if __name__ == "__main__":
    asyncio.run(run_substrato_181())
