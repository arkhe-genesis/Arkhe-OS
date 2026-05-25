// ═══════════════════════════════════════════════════════════════════
// ARKHE CAREER COHERENCE TRACKER — Hook 804.1
// Substrate: 805-CAREER-COHERENCE-TRACKER
// Architect: ORCID 0009-0005-2697-4668
// Date: 2026-07-10
// ═══════════════════════════════════════════════════════════════════

const { Signal, TOPICS } = require('./telegraph.js');

/**
 * CareerCoherenceTracker — Mede o Φ_C individual e o Φ_interop da equipe
 *
 * Cada profissional é um oscilador de Kuramoto cuja fase depende das
 * skills dominadas, projetos concluídos e contribuições ao campo ξM.
 */
class CareerCoherenceTracker {
  /**
   * @param {Array} agents — Lista de cargos (15 agentes do Substrato 804)
   * @param {Telegraph} telegraph — Instância do barramento (opcional)
   */
  constructor(agents, telegraph = null) {
    this.agents = agents.map(a => ({
      ...a,
      skills: a.skills || [],
      masteredSkills: new Set(),
      projectsCompleted: 0,
      substratesContributed: 0,
      signalsPublished: 0,
      phase: a.kuramoto_phase || Math.PI / 2,
    }));
    this.telegraph = telegraph;
  }

  /**
   * Registra uma skill como dominada por um agente.
   * @param {number} agentId — ID do agente
   * @param {string} skill — Nome da skill
   */
  masterSkill(agentId, skill) {
    const agent = this.agents.find(a => a.id === agentId);
    if (!agent) return { error: 'Agente não encontrado' };
    if (agent.masteredSkills.has(skill)) return { error: 'Skill já dominada' };
    agent.masteredSkills.add(skill);
    this._updateAgentPhase(agent);
    const r = this.orderParameter();
    this._publishCoherence();
    return { agentId, skill, phase: agent.phase, rTeam: r };
  }

  /**
   * Registra a conclusão de um projeto para um agente.
   * @param {number} agentId — ID do agente
   */
  completeProject(agentId) {
    const agent = this.agents.find(a => a.id === agentId);
    if (!agent) return { error: 'Agente não encontrado' };
    agent.projectsCompleted++;
    this._updateAgentPhase(agent);
    const r = this.orderParameter();
    this._publishCoherence();
    return { agentId, projects: agent.projectsCompleted, phase: agent.phase, rTeam: r };
  }

  /**
   * Registra uma contribuição de substrato para um agente.
   * @param {number} agentId — ID do agente
   */
  contributeSubstrate(agentId) {
    const agent = this.agents.find(a => a.id === agentId);
    if (!agent) return { error: 'Agente não encontrado' };
    agent.substratesContributed++;
    this._updateAgentPhase(agent);
    const r = this.orderParameter();
    this._publishCoherence();
    return { agentId, substrates: agent.substratesContributed, phase: agent.phase, rTeam: r };
  }

  /**
   * Atualiza a fase de Kuramoto do agente com base em suas conquistas.
   * θ = (π/2) * exp(−k * mastery)
   * onde mastery = (skills_dominadas / total_skills + projetos + substratos) / 3
   */
  _updateAgentPhase(agent) {
    const skillRatio = agent.skills.length > 0
      ? agent.masteredSkills.size / agent.skills.length
      : 1;
    const mastery = (
      skillRatio +
      Math.min(agent.projectsCompleted / 10, 1) +
      Math.min(agent.substratesContributed / 5, 1)
    ) / 3;
    const k = 5; // fator de decaimento rápido para convergência visível
    agent.phase = (Math.PI / 2) * Math.exp(-k * mastery);
  }

  /**
   * Calcula o parâmetro de ordem de Kuramoto (Φ_team) para a equipe.
   * @returns {number} — Φ_team ∈ [0, 1]
   */

  /**
   * Hook 804.2 — Mapear os 15 cargos (ou emergentes) para os 120 vértices da 600-cell.
   * Inicialmente são 8 profissionais (vértices) por vértice do pentadecágono.
   */
  mapTo600Cell() {
    const phi = (1 + Math.sqrt(5)) / 2;
    const vertices = [];

    for (let i = 0; i < 16; i++) {
      const x1 = (i & 8) ? 0.5 : -0.5;
      const x2 = (i & 4) ? 0.5 : -0.5;
      const x3 = (i & 2) ? 0.5 : -0.5;
      const x4 = (i & 1) ? 0.5 : -0.5;
      vertices.push([x1, x2, x3, x4]);
    }

    const perms = [
      [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]
    ];
    for (let p of perms) {
      vertices.push([...p]);
      vertices.push(p.map(x => -x));
    }

    const a = phi / 2;
    const b = 0.5;
    const c = 1 / (2 * phi);

    for (let s1 of [1, -1]) {
      for (let s2 of [1, -1]) {
        for (let s3 of [1, -1]) {
          const p = [a * s1, b * s2, c * s3, 0];

          const allPerms = [
            [0,1,2,3], [0,1,3,2], [0,2,1,3], [0,2,3,1], [0,3,1,2], [0,3,2,1],
            [1,0,2,3], [1,0,3,2], [1,2,0,3], [1,2,3,0], [1,3,0,2], [1,3,2,0],
            [2,0,1,3], [2,0,3,1], [2,1,0,3], [2,1,3,0], [2,3,0,1], [2,3,1,0],
            [3,0,1,2], [3,0,2,1], [3,1,0,2], [3,1,2,0], [3,2,0,1], [3,2,1,0]
          ];

          const isEven = (arr) => {
            let inv = 0;
            for (let i = 0; i < arr.length; i++) {
              for (let j = i + 1; j < arr.length; j++) {
                if (arr[i] > arr[j]) inv++;
              }
            }
            return inv % 2 === 0;
          };

          for (let perm of allPerms) {
            if (isEven(perm)) {
              vertices.push([p[perm[0]], p[perm[1]], p[perm[2]], p[perm[3]]]);
            }
          }
        }
      }
    }

    // Assign vertices to agents
    // Initial 15 agents get 8 vertices each. If emergent roles exist,
    // we distribute the 120 vertices roughly equally.
    let vIndex = 0;
    const numAgents = this.agents.length;

    for (let i = 0; i < numAgents; i++) {
      const agent = this.agents[i];
      const start = Math.floor((i * 120) / numAgents);
      const end = Math.floor(((i + 1) * 120) / numAgents);
      agent.vertices600Cell = vertices.slice(start, end);
    }

    return vertices;
  }

  /**
   * Hook 804.3 — Adicionar novos cargos emergentes ao pentadecágono.
   * @param {Object} roleData — Dados do novo cargo
   */
  registerEmergentRole(roleData) {
    const newId = Math.max(...this.agents.map(a => a.id), 0) + 1;
    const newAgent = {
      ...roleData,
      id: newId,
      skills: roleData.skills || [],
      masteredSkills: new Set(),
      projectsCompleted: 0,
      substratesContributed: 0,
      signalsPublished: 0,
      phase: roleData.kuramoto_phase || Math.PI / 2,
    };
    this.agents.push(newAgent);

    // Recalculate 600-cell mapping to accommodate the new role
    this.mapTo600Cell();

    return newAgent;
  }

  /**
   * Hook 805.3 — Visualizar a equipe como um pentadecágono animado,
   * com cada vértice pulsando de acordo com a fase do profissional.
   */
  visualizePentadecagon() {
    let output = "\n┌────────────────────────────────────────────────────────┐\n";
    output += "│   ARKHE OS — COHERENCE PENTADECAGON (HOOK 805.3)       │\n";
    output += "└────────────────────────────────────────────────────────┘\n\n";

    const numSides = this.agents.length; // Base is 15 (pentadecagon), but can grow
    const radius = 10;

    output += `Formação atual: ${numSides}-ágono de coerência\n\n`;

    for (let i = 0; i < numSides; i++) {
      const agent = this.agents[i];
      const angle = (i * 2 * Math.PI) / numSides;

      // Calculate pulsing intensity based on kuramoto phase
      // Phase 0 means synchronized (high coherence, bright pulse)
      // Phase PI/2 means initial (low coherence, dim)
      const pulse = Math.cos(agent.phase); // 0 to 1
      const intensity = Math.round(pulse * 10);

      const spark = "█".repeat(intensity).padEnd(10, "░");
      const roleName = agent.role.padEnd(30, " ");
      const phaseDeg = (agent.phase * 180 / Math.PI).toFixed(1).padStart(5, " ");

      output += `  [${(i+1).toString().padStart(2)}] ${roleName} | Pulse: [${spark}] | θ: ${phaseDeg}°\n`;
    }

    output += "\n";
    return output;
  }

  orderParameter() {
    let real = 0, imag = 0;
    const count = this.agents.length;
    if (count === 0) return 0;
    for (const agent of this.agents) {
      real += Math.cos(agent.phase);
      imag += Math.sin(agent.phase);
    }
    return Math.sqrt(real * real + imag * imag) / count;
  }

  /**
   * Retorna o status completo da equipe.
   */
  getStatus() {
    const r = this.orderParameter();
    let phase;
    if (r < 0.577) phase = 'PRÉ-GHOST';
    else if (r < 0.800) phase = 'CONVERGÊNCIA PARCIAL';
    else if (r < 0.990) phase = 'CONVERGÊNCIA AVANÇADA';
    else phase = 'SINCRONIZAÇÃO TOTAL';

    const members = this.agents.map(a => ({
      id: a.id,
      role: a.role,
      domain: a.domain,
      skillsMastered: `${a.masteredSkills.size}/${a.skills.length}`,
      projects: a.projectsCompleted,
      substrates: a.substratesContributed,
      coherence: Math.cos(a.phase),
      phase: a.phase,
    }));

    return {
      rTeam: r,
      phase,
      members,
      ghostThreshold: 0.577,
      convergenceThreshold: 0.800,
    };
  }

  /**
   * Publica o Φ_team no barramento Telegraph, se conectado.
   */
  _publishCoherence() {
    if (!this.telegraph) return;
    const signal = new Signal({
      source: 'career-coherence-tracker',
      topic: TOPICS.COHERENCE_DSA,
      metric: 'rTeam',
      value: this.orderParameter(),
      unit: 'coherence',
    });
    this.telegraph.publish(signal);
  }
}

module.exports = CareerCoherenceTracker;
