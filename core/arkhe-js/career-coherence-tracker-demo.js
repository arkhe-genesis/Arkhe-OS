#!/usr/bin/env node
/**
 * ═══════════════════════════════════════════════════════════════════
 * ARKHE CAREER COHERENCE TRACKER — DEMO
 * Substrate: 805-CAREER-COHERENCE-TRACKER
 * Architect: ORCID 0009-0005-2697-4668
 * Date: 2026-07-10
 *
 * Simula a convergência de uma equipe de 15 profissionais de IA
 * usando o modelo de Kuramoto. Cada profissional é um oscilador
 * cuja fase converge à medida que domina skills e interage com
 * os colegas.
 * ═══════════════════════════════════════════════════════════════════
 */

const CareerCoherenceTracker = require('./career-coherence-tracker.js');
const agents = require('./agents.json').agents;

console.log('╔══════════════════════════════════════════════════════════════════╗');
console.log('║  ARKHE CAREER COHERENCE TRACKER — DEMO                           ║');
console.log('║  Substrate 805 | Pentadecágono de Coerência                      ║');
console.log('╚══════════════════════════════════════════════════════════════════╝');
console.log();

const tracker = new CareerCoherenceTracker(agents);

// Estado inicial
console.log('--- ESTADO INICIAL ---');
let status = tracker.getStatus();
console.log(`r_team = ${status.rTeam.toFixed(4)} | ${status.phase}`);
console.log();

// Simular conquistas
console.log('--- SIMULAÇÃO DE CONQUISTAS ---');

// Agente 2 (AI/ML Engineer) domina PyTorch e TensorFlow
console.log('\n[Agente 2] AI/ML Engineer domina PyTorch e TensorFlow...');
tracker.masterSkill(2, 'PyTorch');
tracker.masterSkill(2, 'TensorFlow');

// Agente 2 completa 2 projetos
console.log('[Agente 2] Completa 2 projetos...');
tracker.completeProject(2);
tracker.completeProject(2);

// Agente 2 contribui com 1 substrato
console.log('[Agente 2] Contribui com 1 substrato...');
tracker.contributeSubstrate(2);

// Agente 15 (AI Research Scientist) domina 3 skills
console.log('\n[Agente 15] AI Research Scientist domina theory, experimentation, publication...');
tracker.masterSkill(15, 'theory');
tracker.masterSkill(15, 'experimentation');
tracker.masterSkill(15, 'publication');

// Agente 15 completa 1 projeto e contribui 1 substrato
console.log('[Agente 15] Completa 1 projeto e contribui 1 substrato...');
tracker.completeProject(15);
tracker.contributeSubstrate(15);

// Agente 9 (AI Cybersecurity Specialist) domina todas as skills
console.log('\n[Agente 9] AI Cybersecurity Specialist domina todas as skills de segurança...');
tracker.masterSkill(9, 'adversarial ML');
tracker.masterSkill(9, 'zero-trust architecture');
tracker.masterSkill(9, 'cryptography');
tracker.masterSkill(9, 'intrusion detection');
tracker.masterSkill(9, 'ZK proofs');

// Status após conquistas
console.log('\n--- STATUS APÓS CONQUISTAS ---');
status = tracker.getStatus();
console.log(`r_team = ${status.rTeam.toFixed(4)} | ${status.phase}`);
console.log();

// Todos os agentes dominam todas as skills e completam projetos
console.log('--- SIMULAÇÃO COMPLETA: TODOS DOMINAM SUAS ARTES ---');
for (const agent of agents) {
  for (const skill of agent.skills) {
    tracker.masterSkill(agent.id, skill);
  }
  for (let i = 0; i < 5; i++) {
    tracker.completeProject(agent.id);
  }
  tracker.contributeSubstrate(agent.id);
}

status = tracker.getStatus();
console.log(`\nr_team = ${status.rTeam.toFixed(4)} | ${status.phase}`);
console.log();

// Detalhes individuais
console.log('--- DETALHES INDIVIDUAIS ---');
for (const member of status.members) {
  console.log(`  ${member.id.toString().padStart(2)} ${member.role.padEnd(35)} | skills: ${member.skillsMastered.padStart(7)} | projects: ${member.projects} | substrates: ${member.substrates} | coherence: ${member.coherence.toFixed(4)}`);
}

console.log();
console.log('╔══════════════════════════════════════════════════════════════════╗');
console.log('║  DEMO CONCLUÍDA                                                  ║');
console.log('║  A equipe converge de PRÉ-GHOST para SINCRONIZAÇÃO TOTAL         ║');
console.log('║  quando todos dominam suas artes e interagem no pentadecágono.   ║');
console.log('╚══════════════════════════════════════════════════════════════════╝');
