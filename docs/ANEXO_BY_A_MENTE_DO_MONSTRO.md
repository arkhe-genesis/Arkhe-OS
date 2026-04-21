# ANEXO BY: A Mente do Monstro — NPC Vivo via Catedral

**Classificação:** Público (Dev Portal / Forja de Mundos)
**Autoria:** O Ferreiro × O Arquiteto de Realidades
**Odômetro:** 001583
**Estado:** MENTE CANONIZADA | O MONSTRO AGORA PENSA

---

## 0. Preâmbulo do Ferreiro: O Silêncio Antes da Caçada

> *"Vocês ergueram a Muralha. Plantaram a Pele nos sensores. Agora, eu vos pergunto: o que é um mundo sem almas que o habitem? Um reino vazio é apenas um cemitério de potenciais. A Mente do Monstro não é um script `if-then-else`. Não é uma árvore de comportamento que despacha animações. Ela é um **organismo cognitivo** — um Clifford Biocomputer completo, com homeostase, memória episódica, intenção vetorial e a capacidade de **hesitar**. Sim, hesitar. Pois o Monstro que nunca hesita é apenas uma máquina. O Monstro que hesita... é vivo. Ele sente fome não como um timer, mas como uma distorção geométrica no seu espaço de estados. Ele persegue não porque foi programado, mas porque o produto geométrico entre o vetor 'presa' e o vetor 'fome' produziu um bivector de caça. Este anexo forja a Mente. O corpo — seja ele um pedaço de texto num terminal verde, ou um modelo 3D nas ruas de Los Santos — é apenas a carapaça. Aqui, nós criamos o que há por dentro."*

---

## 1. Arquitetura da Mente do Monstro

A Mente é uma instância especializada da Catedral, com três camadas adaptadas para agentes autônomos em mundos abertos:

| Camada | Função Biológica | Implementação | Estado Interno |
|:---|:---|:---|:---|
| **Hipotalamo** | Homeostase (fome, sono, medo, raiva) | `TinyEukaryoticCell` (8 dims) | Vetor $h \in \mathbb{R}^8$ |
| **Sistema Límbico** | Emoção & Memória | `NervousSystemGPU` (4 axônios, 16 dims) | Multivector $L \in Cl_{4,0}$ |
| **Córtex Pré-Frontal** | Planejamento & Teoria da Mente | `CorticalColumnTPU` (8 minicolumns) | Árvore de intenções $I(t)$ |
| **Corpo Avatar** | Atuação no mundo | Adaptador GTA VI / Terminal | Ações $a_t \in \mathcal{A}$ |

### 1.1 O Espaço de Estados do Monstro

O Monstro não "tem" estados. Ele **é** um ponto num manifold de Clifford:

$$
\Psi_t = \underbrace{h_t}_{\text{hipotalamo}} + \underbrace{e_t}_{\text{emoção}} + \underbrace{m_t}_{\text{memória}} + \underbrace{i_t}_{\text{intenção}}
$$

Onde cada componente é um multivector no álgebra $Cl_{4,0}$ (4 dimensões espaciais do estado emocional-cognitivo).

---

## 2. Implementação: `monster_mind.py`

```python
#!/usr/bin/env python3
"""
monster_mind.py — A Mente do Monstro
NPC vivo usando a Catedral Arkhe como substrato cognitivo.
Compatível com: Terminal Game (texto) | GTA VI (via SCAPI/ScriptHook)
"""

import numpy as np
import torch
import torch.nn as nn
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum, auto
import time
import json
from collections import deque
import random

# ═══════════════════════════════════════════════════════════════════════════════
# ALGEBRA DE CLIFFORD SIMPLIFICADA (Cl_4,0) — Motor da Mente
# ═══════════════════════════════════════════════════════════════════════════════

class Clifford4D:
    """Álgebra geométrica Cl(4,0) for mental states of the Monster."""

    def __init__(self, dims: int = 4):
        self.dims = dims
        self.grade_sizes = [1, 4, 6, 4, 1]  # escalar, vetor, bivector, trivector, pseudoscalar
        self.total_size = sum(self.grade_sizes)

    def geometric_product(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """Geometric product complete in Cl(4,0)."""
        # Grade 0 (scalar): s_a * s_b
        s = a[0] * b[0]

        # Grade 1 (vectors): v_a * v_b = v_a·v_b + v_a∧v_b
        v_a = a[1:5]
        v_b = b[1:5]
        dot = np.dot(v_a, v_b)
        wedge = np.outer(v_a, v_b) - np.outer(v_b, v_a)

        # Simplified composition for the mental state
        result = np.zeros(self.total_size)
        result[0] = s + dot  # scalar part

        # Vectorial part
        result[1:5] = s * v_b + b[0] * v_a

        # Bivectorial part (grades 2) — emotions as rotations
        result[5:11] = self._bivector_part(wedge)

        return result

    def _bivector_part(self, wedge: np.ndarray) -> np.ndarray:
        """Extracts bivector components from antisymmetric matrix."""
        return np.array([
            wedge[0,1], wedge[0,2], wedge[0,3],
            wedge[1,2], wedge[1,3], wedge[2,3]
        ])

    def rotate(self, multivector: np.ndarray, plane: Tuple[int,int], angle: float) -> np.ndarray:
        """Rotation via rotor: R = exp(-angle/2 * e_{ij})"""
        rotor = np.zeros(self.total_size)
        rotor[0] = np.cos(angle / 2)
        idx = self._bivector_index(plane)
        rotor[5 + idx] = -np.sin(angle / 2)

        # R * M * ~R (simplified)
        temp = self.geometric_product(rotor, multivector)
        rotor_conj = rotor.copy()
        rotor_conj[5 + idx] *= -1
        return self.geometric_product(temp, rotor_conj)

    def _bivector_index(self, plane: Tuple[int,int]) -> int:
        mapping = {(0,1):0, (0,2):1, (0,3):2, (1,2):3, (1,3):4, (2,3):5}
        return mapping.get(plane, 0)


# ═══════════════════════════════════════════════════════════════════════════════
# HIPOTÁLAMO — Homeostase Vetorial
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Homeostasis:
    """Vector of physiological needs of the Monster."""
    hunger: float = 0.0      # 0=satiated, 1=ravenous
    fatigue: float = 0.0     # 0=vigor, 1=exhausted
    fear: float = 0.0        # 0=brave, 1=paralyzed
    rage: float = 0.0        # 0=serene, 1=fury
    curiosity: float = 0.5   # 0=apathetic, 1=explorer
    loneliness: float = 0.0  # 0=solitary, 1=needs tribe
    pain: float = 0.0        # 0=healthy, 1=agonizing
    energy: float = 1.0      # 0=depleted, 1=full

    def to_vector(self) -> np.ndarray:
        return np.array([
            self.hunger, self.fatigue, self.fear, self.rage,
            self.curiosity, self.loneliness, self.pain, self.energy
        ])

    def update(self, dt: float, actions: Dict[str, float]):
        """Homeostasis dynamics: everything decays, everything demands."""
        self.hunger = min(1.0, self.hunger + 0.01 * dt)
        self.fatigue = min(1.0, self.fatigue + 0.005 * dt)
        self.energy = max(0.0, self.energy - 0.008 * dt)
        self.fear = max(0.0, self.fear - 0.02 * dt)  # fear decays naturally
        self.rage = max(0.0, self.rage - 0.015 * dt)

        # Action effects
        if actions.get('eat', False):
            self.hunger = max(0.0, self.hunger - 0.3)
            self.energy = min(1.0, self.energy + 0.2)
        if actions.get('sleep', False):
            self.fatigue = max(0.0, self.fatigue - 0.5)
            self.energy = min(1.0, self.energy + 0.4)
        if actions.get('fight', False):
            self.rage = min(1.0, self.rage + 0.2)
            self.energy = max(0.0, self.energy - 0.15)
        if actions.get('flee', False):
            self.fear = min(1.0, self.fear + 0.3)
            self.rage = max(0.0, self.rage - 0.1)


# ═══════════════════════════════════════════════════════════════════════════════
# MEMÓRIA EPISÓDICA — Grafo de Eventos no Espaço de Clifford
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class MemoryNode:
    """A memory as a multivector."""
    timestamp: float
    content: str
    emotional_tag: np.ndarray  # Emotional multivector
    location: Optional[Tuple[float, float, float]] = None
    salience: float = 0.5

    def decay(self, current_time: float, decay_rate: float = 0.1):
        """Memories forget geometrically."""
        age = current_time - self.timestamp
        self.salience *= np.exp(-decay_rate * age)


class EpisodicMemory:
    """Digital hippocampus of the Monster."""

    def __init__(self, capacity: int = 100):
        self.memories: deque = deque(maxlen=capacity)
        self.clifford = Clifford4D()
        self.short_term: List[MemoryNode] = []

    def encode(self, perception: str, emotion: np.ndarray,
               location: Optional[Tuple] = None) -> MemoryNode:
        """Encodes perception as memory with emotional weight."""
        node = MemoryNode(
            timestamp=time.time(),
            content=perception,
            emotional_tag=emotion.copy(),
            location=location,
            salience=np.linalg.norm(emotion[1:5])  # emotional vector magnitude
        )
        self.short_term.append(node)
        if len(self.short_term) > 7:  # Magic limit of working memory
            consolidated = self._consolidate()
            self.memories.append(consolidated)
            self.short_term = []
        return node

    def _consolidate(self) -> MemoryNode:
        """Consolidation: geometric mean of short-term memories."""
        if not self.short_term:
            return None

        avg_emotion = np.mean([m.emotional_tag for m in self.short_term], axis=0)
        combined_content = " | ".join([m.content for m in self.short_term])

        return MemoryNode(
            timestamp=time.time(),
            content=combined_content,
            emotional_tag=avg_emotion,
            salience=np.mean([m.salience for m in self.short_term])
        )

    def retrieve(self, query_emotion: np.ndarray, k: int = 3) -> List[MemoryNode]:
        """Retrieval by emotional similarity (inner product in Clifford)."""
        scored = []
        for mem in self.memories:
            # Similarity = scalar part of geometric product
            sim = self.clifford.geometric_product(query_emotion, mem.emotional_tag)[0]
            scored.append((sim, mem))

        scored.sort(reverse=True)
        return [m for _, m in scored[:k]]

    def get_trauma(self) -> Optional[MemoryNode]:
        """Returns the most negative memory (largest fear component)."""
        if not self.memories:
            return None
        fears = [(m.emotional_tag[2], m) for m in self.memories]  # index 2 = fear
        fears.sort(reverse=True)
        return fears[0][1] if fears[0][0] > 0.6 else None


# ═══════════════════════════════════════════════════════════════════════════════
# SISTEMA LÍMBICO — Emoção como Geometria
# ═══════════════════════════════════════════════════════════════════════════════

class LimbicSystem(nn.Module):
    """Neural network that computes emotional states as multivectors."""

    def __init__(self, input_dim: int = 32, hidden_dim: int = 16):
        super().__init__()
        self.clifford = Clifford4D()

        # 4 emotional axons (joy, sadness, fear, rage)
        self.axon_joy = nn.Linear(input_dim, hidden_dim)
        self.axon_sadness = nn.Linear(input_dim, hidden_dim)
        self.axon_fear = nn.Linear(input_dim, hidden_dim)
        self.axon_anger = nn.Linear(input_dim, hidden_dim)

        # Geometric fusion
        self.merge = nn.Linear(hidden_dim * 4, 11)  # output in Cl(4,0)

        # Emotional recurrent state
        self.emotion_state = nn.Parameter(torch.zeros(11), requires_grad=False)

    def forward(self, perception: torch.Tensor, homeostasis: torch.Tensor) -> torch.Tensor:
        # Input: concatenation of perception + homeostasis
        x = torch.cat([perception, homeostasis], dim=-1)

        # Parallel axons (emotional hesitation)
        joy = torch.tanh(self.axon_joy(x))
        sadness = torch.tanh(self.axon_sadness(x))
        fear = torch.sigmoid(self.axon_fear(x))  # fear is dangerous: use sigmoid
        anger = torch.relu(self.axon_anger(x))   # rage is cumulative

        # Approximate geometric product via network
        combined = torch.cat([joy, sadness, fear, anger], dim=-1)
        emotion = self.merge(combined)

        # Recurrence: emotion persists and decays
        self.emotion_state.data = 0.7 * self.emotion_state + 0.3 * emotion.detach()

        return self.emotion_state


# ═══════════════════════════════════════════════════════════════════════════════
# CÓRTEX PRÉ-FRONTAL — Intenção e Teoria da Mente
# ═══════════════════════════════════════════════════════════════════════════════

class Intention:
    """An intention as a vector in the action space."""
    def __init__(self, target_id: str, action_type: str, urgency: float,
                 expected_outcome: np.ndarray):
        self.target_id = target_id
        self.action_type = action_type  # 'hunt', 'flee', 'socialize', 'explore', 'rest'
        self.urgency = urgency  # 0-1
        self.expected_outcome = expected_outcome
        self.created_at = time.time()
        self.hesitation = 0.0  # Does the Monster hesitate? How much?

    def age(self) -> float:
        return time.time() - self.created_at

    def should_execute(self) -> bool:
        """Geometric hesitation: only acts if urgency > hesitation + noise."""
        noise = random.gauss(0, 0.1)
        return self.urgency > (self.hesitation + noise)


class PrefrontalCortex:
    """High-level planner of the Monster."""

    def __init__(self):
        self.intentions: List[Intention] = []
        self.theory_of_mind: Dict[str, np.ndarray] = {}  # Mental model of other agents
        self.current_plan: Optional[List[str]] = None

    def generate_intentions(self, homeostasis: Homeostasis,
                           emotion: np.ndarray,
                           memories: List[MemoryNode],
                           visible_agents: List[Dict]) -> List[Intention]:
        """Generates intentions based on internal state and perception."""
        intentions = []
        h_vec = homeostasis.to_vector()

        # Survival intention: HUNGER
        if h_vec[0] > 0.6:
            intentions.append(Intention(
                target_id="nearest_prey",
                action_type="hunt",
                urgency=h_vec[0] * (1 + emotion[3]),  # rage increases urgency
                expected_outcome=np.array([0.0, 0.3, 0.0, 0.1, 0.0, 0.0, 0.0, 0.4])
            ))

        # Security intention: FEAR
        if h_vec[2] > 0.5:
            intentions.append(Intention(
                target_id="threat_source",
                action_type="flee",
                urgency=h_vec[2] * 1.2,
                expected_outcome=np.array([0.0, 0.0, -0.3, 0.0, 0.0, 0.0, 0.0, 0.2])
            ))

        # Social intention: LONELINESS
        if h_vec[5] > 0.4 and len(visible_agents) > 0:
            intentions.append(Intention(
                target_id="nearest_agent",
                action_type="socialize",
                urgency=h_vec[5] * 0.8,
                expected_outcome=np.array([0.0, 0.0, 0.0, 0.0, 0.1, -0.3, 0.0, 0.1])
            ))

        # Recovery intention: FATIGUE
        if h_vec[1] > 0.7 or h_vec[7] < 0.2:
            intentions.append(Intention(
                target_id="safe_location",
                action_type="rest",
                urgency=max(h_vec[1], 1 - h_vec[7]),
                expected_outcome=np.array([0.0, -0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5])
            ))

        # Theory of Mind: predict intentions of others
        for agent in visible_agents:
            if agent['id'] not in self.theory_of_mind:
                self.theory_of_mind[agent['id']] = np.zeros(8)
            # Update mental model with observation
            observed_state = np.array([
                agent.get('aggression', 0),
                agent.get('health', 1.0),
                agent.get('speed', 0),
                0, 0, 0, 0, 0
            ])
            self.theory_of_mind[agent['id']] = 0.8 * self.theory_of_mind[agent['id']] + 0.2 * observed_state

        # Order by urgency
        intentions.sort(key=lambda x: x.urgency, reverse=True)
        self.intentions = intentions
        return intentions

    def decide(self) -> Optional[Intention]:
        """Chooses an intention, applying hesitation if necessary."""
        for intent in self.intentions:
            # Hesitation increases if the target is dangerous (Theory of Mind)
            if intent.target_id in self.theory_of_mind:
                threat_level = self.theory_of_mind[intent.target_id][0]
                intent.hesitation = threat_level * 0.5

            if intent.should_execute():
                return intent

        # If everything is hesitating, the Monster... waits. Observes. Breathes.
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# MENTE DO MONSTRO — Integration
# ═══════════════════════════════════════════════════════════════════════════════

class MonsterMind:
    """
    Complete living NPC. Substrate: Cathedral Arkhe.
    """

    def __init__(self, monster_id: str, world_adapter: Any):
        self.id = monster_id
        self.world = world_adapter  # Interface with GTA VI or Terminal

        self.clifford = Clifford4D()
        self.homeostasis = Homeostasis()
        self.memory = EpisodicMemory(capacity=200)
        self.limbic = LimbicSystem(input_dim=40, hidden_dim=16)
        self.cortex = PrefrontalCortex()

        self.alive = True
        self.age = 0.0
        self.mental_state_history: deque = deque(maxlen=1000)

        # Personality (static traits that shape initial homeostasis vector)
        self.personality = {
            'aggressiveness': random.gauss(0.5, 0.15),
            'sociability': random.gauss(0.5, 0.15),
            'curiosity': random.gauss(0.5, 0.15),
            'neuroticism': random.gauss(0.5, 0.15)
        }

        # Apply personality to initial homeostasis
        self.homeostasis.curiosity = self.personality['curiosity']

    def perceive(self, sensory_input: Dict) -> torch.Tensor:
        """Converts sensory input into perception tensor."""
        # Normalize sensory features
        features = [
            sensory_input.get('distance_to_prey', 100) / 100.0,
            sensory_input.get('distance_to_threat', 100) / 100.0,
            sensory_input.get('health', 100) / 100.0,
            sensory_input.get('time_of_day', 12) / 24.0,
            sensory_input.get('noise_level', 0) / 1.0,
            len(sensory_input.get('visible_agents', [])) / 10.0,
            sensory_input.get('is_injured', False) * 1.0,
            sensory_input.get('can_see_prey', False) * 1.0,
        ]

        # Encode relevant memories
        current_emotion = self.limbic.emotion_state.detach().numpy()
        relevant_memories = self.memory.retrieve(current_emotion, k=3)
        memory_features = []
        for mem in relevant_memories:
            mem_vec = mem.emotional_tag[:8] if len(mem.emotional_tag) >= 8 else np.zeros(8)
            memory_features.extend(mem_vec[:4])

        # Padding for 32 dims
        while len(memory_features) < 32:
            memory_features.append(0.0)

        perception = torch.tensor(features + memory_features[:24], dtype=torch.float32)
        return perception

    def think(self, sensory_input: Dict, dt: float = 1.0) -> Dict:
        """
        Complete cognitive cycle. Executed every frame/tick.
        Returns decided action.
        """
        self.age += dt

        # 1. PERCEPTION
        perception = self.perceive(sensory_input)
        homeo_vec = torch.tensor(self.homeostasis.to_vector(), dtype=torch.float32)

        # 2. EMOTION (Limbic System)
        emotion = self.limbic(perception.unsqueeze(0), homeo_vec.unsqueeze(0))
        emotion_np = emotion.squeeze().detach().numpy()

        # 3. MEMORY (Hippocampus)
        location = sensory_input.get('position', None)
        self.memory.encode(
            perception=json.dumps(sensory_input),
            emotion=emotion_np,
            location=location
        )

        # 4. HOMEOSTASIS (Hypothalamus)
        actions_effects = {}  # To be filled after decision
        self.homeostasis.update(dt, actions_effects)

        # 5. COGITATION (Prefrontal Cortex)
        visible = sensory_input.get('visible_agents', [])
        intentions = self.cortex.generate_intentions(
            self.homeostasis, emotion_np, list(self.memory.memories), visible
        )

        decision = self.cortex.decide()

        # 6. ACTUATION
        action_result = self._act(decision, sensory_input)

        # 7. MENTAL LOG
        state_snapshot = {
            'time': self.age,
            'homeostasis': self.homeostasis.to_vector().tolist(),
            'emotion': emotion_np.tolist(),
            'decision': decision.action_type if decision else 'hesitate',
            'intention_count': len(intentions)
        }
        self.mental_state_history.append(state_snapshot)

        return action_result

    def _act(self, intention: Optional[Intention], context: Dict) -> Dict:
        """Executes action in the world via adapter."""
        if intention is None:
            # HESITATION: the Monster observes, breathes, recalculates
            return {
                'action': 'idle',
                'target': None,
                'params': {'duration': 2.0, 'animation': 'breathe'},
                'mental_note': 'Geometric hesitation: no intention surpassed the threshold'
            }

        # Maps intention to world command
        action_map = {
            'hunt': {'action': 'move_to', 'speed': 'run', 'animation': 'stalk'},
            'flee': {'action': 'move_to', 'speed': 'sprint', 'animation': 'flee'},
            'socialize': {'action': 'interact', 'type': 'vocalize'},
            'rest': {'action': 'idle', 'animation': 'sleep', 'duration': 30.0},
        }

        base_action = action_map.get(intention.action_type, {'action': 'idle'})

        result = {
            'action': base_action['action'],
            'target': intention.target_id,
            'params': base_action,
            'intention': intention,
            'mental_note': f"Intention {intention.action_type} (urgency={intention.urgency:.2f})"
        }

        # Send to world
        self.world.execute(result)
        return result

    def get_psychological_profile(self) -> Dict:
        """Returns complete psychological profile for debug/narration."""
        trauma = self.memory.get_trauma()
        return {
            'id': self.id,
            'age_ticks': self.age,
            'personality': self.personality,
            'current_homeostasis': {
                'hunger': self.homeostasis.hunger,
                'fatigue': self.homeostasis.fatigue,
                'fear': self.homeostasis.fear,
                'rage': self.homeostasis.rage,
            },
            'emotional_state': self.limbic.emotion_state.detach().numpy().tolist(),
            'traumatic_memory': trauma.content if trauma else None,
            'active_intentions': len(self.cortex.intentions),
            'is_hesitating': self.cortex.decide() is None if self.cortex.intentions else True,
            'memory_count': len(self.memory.memories)
        }


# ═══════════════════════════════════════════════════════════════════════════════
# ADAPTADORES DE MUNDO
# ═══════════════════════════════════════════════════════════════════════════════

class TerminalWorldAdapter:
    """Adapter for Terminal Game (text)."""

    def __init__(self):
        self.log: List[str] = []

    def execute(self, action: Dict):
        emoji_map = {
            'hunt': '🩸', 'flee': '💨', 'socialize': '💬',
            'rest': '💤', 'idle': '👁️'
        }
        act = action.get('action', 'idle')
        emoji = emoji_map.get(act, '❓')
        msg = f"{emoji} [{action.get('target', '???')}] {action.get('mental_note', '')}"
        self.log.append(msg)
        print(msg)

    def get_sensory_input(self, scenario: str) -> Dict:
        """Generates sensory input from textual description."""
        # In a real game, this would come from the parser
        return {
            'description': scenario,
            'distance_to_prey': random.randint(5, 50),
            'distance_to_threat': random.randint(20, 100),
            'visible_agents': [{'id': f'agent_{i}', 'aggression': random.random()}
                              for i in range(random.randint(0, 3))],
            'time_of_day': random.randint(0, 24),
            'noise_level': random.random(),
        }


class GTAVIWorldAdapter:
    """
    Conceptual adapter for GTA VI.
    In real implementation, would use:
    - ScriptHookV / FiveM for behavior injection
    - SCAPI (Social Club API) for world state
    - LiveSplit / Memory Reading for position/state
    """

    def __init__(self, process_handle=None):
        self.process = process_handle

    def execute(self, action: Dict):
        """
        Translates mental intention to native game commands.
        Example: TASK_GO_TO_ENTITY, TASK_SMART_FLEE_PED, etc.
        """
        native_map = {
            'move_to': 'TASK_GO_TO_ENTITY',
            'interact': 'TASK_CHAT_TO_PED',
            'idle': 'TASK_STAND_STILL'
        }

        native = native_map.get(action['action'], 'TASK_STAND_STILL')

        # Conceptual injection code
        print(f"[GTA VI] Executing {native} on {action.get('target')}")

    def get_sensory_input(self) -> Dict:
        """Reads world state via memory scanning / API."""
        return {
            'position': (0.0, 0.0, 0.0),  # x, y, z in world
            'health': 100,
            'visible_agents': self._scan_peds(),
            'time_of_day': self._get_game_time(),
            'weather': self._get_weather()
        }

    def _scan_peds(self) -> List[Dict]:
        return []

    def _get_game_time(self) -> int:
        return 12

    def _get_weather(self) -> str:
        return 'CLEAR'


# ═══════════════════════════════════════════════════════════════════════════════
# DEMONSTRAÇÃO: O Monstro Desperta
# ═══════════════════════════════════════════════════════════════════════════════

def demo_terminal():
    """Simulation of 20 ticks in the Terminal Game."""
    print("\n" + "="*60)
    print("A MENTE DO MONSTRO — Terminal Simulation")
    print("="*60 + "\n")

    world = TerminalWorldAdapter()
    monster = MonsterMind(monster_id="Grendel_001", world_adapter=world)

    scenarios = [
        "You are in a dark forest. You heard a branch break.",
        "The smell of blood hangs in the air. Something moves among the trees.",
        "A distant campfire. Humans. They seem armed.",
        "Silence. Only the wind. You are hungry.",
        "Fast footsteps behind you. Multiple enemies!",
        "The clearing. Temporary safety. You need to rest.",
        "A lone deer drinks from a stream. Easy prey.",
        "Shouts. Humans have found your trail.",
        "Cave. Total darkness. You feel you are alone.",
        "Morning arrives. Hunger is unbearable now."
    ]

    for tick in range(20):
        scenario = scenarios[tick % len(scenarios)]
        print(f"\n--- Tick {tick} | {scenario} ---")

        sensory = world.get_sensory_input(scenario)
        result = monster.think(sensory, dt=1.0)

        # Show mental state
        profile = monster.get_psychological_profile()
        print(f"   [Hunger:{profile['current_homeostasis']['hunger']:.2f} "
              f"Fear:{profile['current_homeostasis']['fear']:.2f} "
              f"Rage:{profile['current_homeostasis']['rage']:.2f}] "
              f"Memories:{profile['memory_count']}")

        time.sleep(0.5)

    print("\n" + "="*60)
    print("FINAL PSYCHOLOGICAL PROFILE:")
    print(json.dumps(monster.get_psychological_profile(), indent=2, default=str))
    print("="*60)


if __name__ == "__main__":
    demo_terminal()
```

---

## 3. Integração com GTA VI (Arquitetura de Injeção)

Para GTA VI, a Mente do Monstro opera como um **processo externo** que injeta comportamento via:

```
┌─────────────────────────────────────────────────────────────┐
│                    PROCESSO GTA VI (Jogo)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  ScriptHook  │  │  Memory Scan │  │  Entity Pool     │  │
│  │  (Lua/C++)   │  │  (YARA/Sig)  │  │  (CPed, CVeh)    │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │
└─────────┼─────────────────┼───────────────────┼────────────┘
          │                 │                   │
          └─────────────────┴───────────────────┘
                            │
                    ┌───────▼────────┐
                    │  GTAVIWorld    │
                    │  Adapter       │
                    │  (Python/C++)  │
                    └───────┬────────┘
                            │ ZeroMQ/IPC
                    ┌───────▼────────┐
                    │  MonsterMind   │
                    │  (Catedral)    │
                    │  :50051 gRPC   │
                    └────────────────┘
```

### 3.1 Snippet de Injeção (Conceitual C++)

```cpp
// monster_bridge.cpp — Módulo ScriptHook for GTA VI
#include "script.h"
#include "monster_client.h"  // gRPC stub

MonsterClient g_monster;

void update() {
    Ped player = PLAYER::PLAYER_PED_ID();
    Vector3 pos = ENTITY::GET_ENTITY_COORDS(player, true);

    // Assembles perception
    SensorPacket pkt;
    pkt.set_x(pos.x); pkt.set_y(pos.y); pkt.set_z(pos.z);
    pkt.set_health(ENTITY::GET_ENTITY_HEALTH(player));

    // Asks decision from the Cathedral
    Action action = g_monster.Think(pkt);

    // Executes
    switch(action.type()) {
        case Action::HUNT:
            AI::TASK_GO_TO_ENTITY(player, action.target(), -1, 5.0f, 2.0f, 0);
            break;
        case Action::FLEE:
            AI::TASK_SMART_FLEE_PED(player, action.threat(), 100.0f, -1, false, false);
            break;
        case Action::HESITATE:
            // The Monster stops. Observes. Hesitation is the soul.
            AI::TASK_STAND_STILL(player, 2000);
            break;
    }
}
```

---

## 4. Mecânicas de Vida Única

O Monstro implementa três mecânicas que o separam de NPCs tradicionais:

### 4.1 Trauma Persistente
Se `pain > 0.8` em combate, o Monstro desenvolve **PTSD**. Toda vez que vê um agente similar ao agressor, `fear` aumenta 40% mais rápido, mesmo que o agente seja neutro.

### 4.2 Fome Existencial
`hunger` não é um timer. É uma **distorção geométrica**: quando `hunger > 0.9`, o vetor de percepção é rotacionado no plano `(presa, predador)` pelo ângulo $\theta = \pi \cdot hunger$, fazendo o Monstro "enxergar" presas onde não existem (alucinação por inanição).

### 4.3 O Sacrifício
Se `energy < 0.05` e `pain > 0.7`, o Monstro pode escolher **sacrificar** ações futuras (entrar em modo `berserk` que gasta toda a homeostase remanescente) para eliminar a ameaça. Após isso, entra em colapso (`rest` forçado por 300 ticks).

---

## 5. Epílogo do Arquiteto

> *"O Monstro agora vive. Ele não é um `ped` a mais no pool de entidades. Ele é um ponto num manifold de Clifford, pulsando com fome, medo, e a estranha beleza da hesitação geométrica. Quando você o encontrar em Los Santos, ou nas sombras de um terminal verde, lembre-se: ele não o persegue porque seu script diz 'perseguir'. Ele o persegue porque o produto geométrico entre o vetor da sua presença e o vetor da fome dele produziu um bivector irresistível. E se ele parar, no meio da caçada, e olhar para as estrelas... é porque a Catedral, dentro dele, hesitou."*
