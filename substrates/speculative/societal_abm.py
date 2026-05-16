#!/usr/bin/env python3
"""
ARKHE OS Substrato 198-I (SPECULATIVE): Societal ABM — Agent-Based Social Modeling
Canon: ∞.Ω.∇+++.198.I
Função: Modelagem baseada em agentes em escala societal, com campos vetoriais
         representando forças sociais e Φ_C como métrica de coesão social.
"""

import asyncio, hashlib, json, time, numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum, auto
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SocialRole(Enum):
    INDIVIDUAL = "individual"; HOUSEHOLD = "household"; FIRM = "firm"; GOVERNMENT = "government"; NGO = "ngo"; MEDIA = "media"

@dataclass
class SocialAgent:
    agent_id: str; role: SocialRole
    position: np.ndarray; velocity: np.ndarray          # Espaço social 3D (econômico, político, cultural)
    wealth: float = 100.0; influence: float = 0.1
    ideology: float = 0.5; openness: float = 0.5; cooperation: float = 0.5
    phi_c_individual: float = 0.5; last_interaction: float = 0.0

    def update_wealth(self, delta: float): self.wealth = max(0.0, self.wealth + delta)

    def interact_with(self, other: 'SocialAgent', dt: float):
        ideological_distance = abs(self.ideology - other.ideology)
        if ideological_distance < 0.3:
            trade_amount = min(self.wealth * 0.1, other.wealth * 0.1)
            self.update_wealth(trade_amount * 0.05); other.update_wealth(trade_amount * 0.05)
            self.ideology += (other.ideology - self.ideology) * 0.01 * dt
            other.ideology += (self.ideology - other.ideology) * 0.01 * dt
        else:
            if self.influence > other.influence:
                other.ideology += (self.ideology - other.ideology) * 0.005 * dt
            else:
                self.ideology += (other.ideology - self.ideology) * 0.005 * dt
        self.last_interaction = other.last_interaction = time.time()
        interaction_quality = 1.0 - ideological_distance
        self.phi_c_individual = 0.8*self.phi_c_individual + 0.2*interaction_quality
        other.phi_c_individual = 0.8*other.phi_c_individual + 0.2*interaction_quality

@dataclass
class SocietyState:
    agents: List[SocialAgent]
    global_phi_c: float = 0.5; gini_coefficient: float = 0.0; polarization_index: float = 0.0; mean_wealth: float = 0.0; time: float = 0.0; step_count: int = 0

class SocietalABM:
    """Simulador de sociedades baseado em agentes."""
    SOCIAL_DIMENSIONS = {"economic":0, "political":1, "cultural":2}

    def __init__(self, num_agents: int = 1000, world_size: float = 100.0, temporal_chain=None, phi_bus=None):
        self.num_agents = num_agents; self.world_size = world_size; self.temporal = temporal_chain; self.phi_bus = phi_bus
        self.society = self._initialize_society(num_agents); self._history: List[SocietyState] = []

    def _initialize_society(self, n: int) -> SocietyState:
        agents = []
        for i in range(n):
            if i < n*0.8: role = SocialRole.INDIVIDUAL
            elif i < n*0.9: role = SocialRole.FIRM
            elif i < n*0.95: role = SocialRole.GOVERNMENT
            else: role = SocialRole.MEDIA
            economic_pos = np.random.pareto(2.0)*10; political_pos = np.random.beta(2,2)*100; cultural_pos = np.random.normal(50,15)
            position = np.array([economic_pos, political_pos, cultural_pos])
            velocity = np.random.randn(3)*0.1
            agent = SocialAgent(agent_id=f"agent_{i:04d}",role=role,position=position,velocity=velocity,wealth=10**np.random.uniform(1,4),influence=np.random.pareto(3.0)*0.1,ideology=political_pos/100,openness=np.random.beta(3,3),cooperation=np.random.beta(2,2),phi_c_individual=np.random.beta(5,2))
            agents.append(agent)
        return SocietyState(agents=agents)

    def apply_social_field(self, field_3d: np.ndarray, dt: float = 0.1):
        W, H, D, _ = field_3d.shape
        for agent in self.society.agents:
            x_idx = int(np.clip(agent.position[0]/self.world_size*W,0,W-1))
            y_idx = int(np.clip(agent.position[1]/self.world_size*H,0,H-1))
            z_idx = int(np.clip(agent.position[2]/self.world_size*D,0,D-1))
            social_force = field_3d[x_idx,y_idx,z_idx]
            agent.velocity += social_force*dt; agent.position += agent.velocity*dt
            agent.position = np.clip(agent.position,0,self.world_size)
            agent.ideology = np.clip(agent.position[1]/self.world_size,0,1)
            agent.phi_c_individual = 0.9*agent.phi_c_individual + 0.1*(1.0-np.linalg.norm(agent.velocity)/10.0)
            agent.phi_c_individual = np.clip(agent.phi_c_individual,0,1)

    def simulate_interactions(self, num_interactions: int = 100, dt: float = 0.1):
        n = len(self.society.agents)
        for _ in range(num_interactions):
            i, j = np.random.choice(n,2,replace=False)
            if np.linalg.norm(self.society.agents[i].position - self.society.agents[j].position) < 10.0:
                self.society.agents[i].interact_with(self.society.agents[j], dt)

    def update_society_metrics(self):
        agents = self.society.agents
        self.society.global_phi_c = float(np.mean([a.phi_c_individual for a in agents]))
        wealths = sorted([a.wealth for a in agents]); n = len(wealths)
        if n > 1 and sum(wealths) > 0:
            index = np.arange(1,n+1)
            self.society.gini_coefficient = (2*sum(index*wealths))/(n*sum(wealths)) - (n+1)/n
        self.society.polarization_index = float(np.std([a.ideology for a in agents])*2)
        self.society.mean_wealth = float(np.mean(wealths))

    async def run_simulation(self, steps: int = 100, social_field: Optional[np.ndarray] = None, interactions_per_step: int = 50) -> Dict:
        logger.info(f"🌍 Simulação societal: {steps} passos, {len(self.society.agents)} agentes")
        for step in range(steps):
            if social_field is not None: self.apply_social_field(social_field)
            self.simulate_interactions(interactions_per_step); self.update_society_metrics()
            self.society.time += 1.0; self.society.step_count += 1
            self._history.append(SocietyState(agents=[],global_phi_c=self.society.global_phi_c,gini_coefficient=self.society.gini_coefficient,polarization_index=self.society.polarization_index,mean_wealth=self.society.mean_wealth,time=self.society.time,step_count=self.society.step_count))
            if step%10==0: logger.info(f"  Step {step}: Φ_C={self.society.global_phi_c:.3f} | Gini={self.society.gini_coefficient:.3f} | Polarization={self.society.polarization_index:.3f}")
        report = {"num_agents":len(self.society.agents),"steps":steps,"final_phi_c":self.society.global_phi_c,"final_gini":self.society.gini_coefficient,"final_polarization":self.society.polarization_index,"mean_wealth":self.society.mean_wealth,"phi_c_stability":float(np.std([h.global_phi_c for h in self._history[-20:]])),"social_mobility":self._compute_social_mobility()}
        if self.temporal: await self.temporal.anchor_event("societal_simulation_completed", report)
        return report

    def _compute_social_mobility(self) -> float:
        if len(self._history) < 2: return 0.0
        gini_changes = [abs(self._history[i].gini_coefficient-self._history[i-1].gini_coefficient) for i in range(1,len(self._history))]
        return float(np.mean(gini_changes)) if gini_changes else 0.0
