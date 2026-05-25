// ═══════════════════════════════════════════════════════════════════
// ARKHE CAREER COHERENCE TRACKER — Hook 804.1
// Substrate: 805-CAREER-COHERENCE-TRACKER
// Architect: ORCID 0009-0005-2697-4668
// Date: 2026-07-10
// ═══════════════════════════════════════════════════════════════════

const { Telegraph } = require('./telegraph.js');

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
    const mastery = (skillRatio + Math.min(agent.projectsCompleted / 10, 1) + Math.min(agent.substratesContributed / 5, 1)) / 3;
    const k = 5; // fator de decaimento rápido para convergência visível
    agent.phase = (Math.PI / 2) * Math.exp(-k * mastery);
  }

  /**
   * Calcula o parâmetro de ordem de Kuramoto (Φ_team) para a equipe.
   * @returns {number} — Φ_team ∈ [0, 1]
   */
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
    const signal = this.telegraph.createSignal(
      'career-coherence-tracker',
      'rTeam',
      this.orderParameter(),
      'coherence'
    );
    this.telegraph.publish('/coherence/dsa', signal);
  }
}

module.exports = CareerCoherenceTracker;
