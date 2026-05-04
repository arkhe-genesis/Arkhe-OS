
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// arkhe-dashboard/src/lib/meditation/coherentMeditation.ts
// Módulo de meditação coerente: neurofeedback coletivo guiado por sincronicidades

import type { SynchronicityPattern } from '@/lib/quantum/quantumSynchronicity';

export interface MeditationSession {
  sessionId: string;
  participants: string[];  // IDs dos participantes
  startTime_ns: number;
  targetOmega: number;  // Ω alvo para a sessão
  currentOmega: number;  // Ω coletivo atual
  synchronicityGuidance: SynchronicityPattern | null;  // Padrão de sincronicidade guiando a sessão
  binauralFrequency: number;  // Frequência de binaural beats em Hz
  arVisualizationEnabled: boolean;
  collectiveCoherence: number;  // Coerência coletiva calculada (0.0-1.0)
  sessionStatus: 'preparing' | 'active' | 'completed' | 'interrupted';
}

export interface ParticipantBiofeedback {
  participantId: string;
  heartRate: number;  // BPM
  gsr: number;  // Resposta galvânica da pele (0.0-1.0)
  brainwaveAlpha: number;  // Potência de ondas alfa (0.0-1.0)
  brainwaveTheta: number;  // Potência de ondas theta (0.0-1.0)
  coherenceScore: number;  // Score de coerência pessoal (0.0-1.0)
  timestamp_ns: number;
}

export interface CoherentMeditationConfig {
  targetOmegaRange: [number, number];  // Faixa alvo para Ω (padrão: [0.92, 0.98])
  synchronicitySensitivity: number;  // Sensibilidade a padrões de sincronicidade (0.0-1.0)
  binauralAdaptationRate: number;  // Taxa de adaptação de binaural beats (0.0-1.0)
  arOverlayOpacity: number;  // Opacidade do overlay AR (0.0-1.0)
  collectiveThreshold: number;  // Threshold para considerar coerência coletiva alcançada
}

export class CoherentMeditationEngine {
  private config: CoherentMeditationConfig;
  private activeSessions = new Map<string, MeditationSession>();
  private participantBiofeedback = new Map<string, ParticipantBiofeedback>();

  constructor(
    config: Partial<CoherentMeditationConfig> = {}
  ) {
    this.config = {
      targetOmegaRange: [0.92, 0.98],
      synchronicitySensitivity: 0.7,
      binauralAdaptationRate: 0.1,
      arOverlayOpacity: 0.6,
      collectiveThreshold: 0.90,
      ...config,
    };
  }

  /**
   * Inicia nova sessão de meditação coerente
   */
  async startMeditationSession(
    sessionId: string,
    participants: string[],
    targetOmega: number
  ): Promise<MeditationSession> {
    // Verificar se targetOmega está na faixa válida
    const [min, max] = this.config.targetOmegaRange;
    if (targetOmega < min || targetOmega > max) {
      throw new Error(`targetOmega deve estar entre ${min} e ${max}`);
    }

    const session: MeditationSession = {
      sessionId,
      participants,
      startTime_ns: Date.now() * 1e6,
      targetOmega,
      currentOmega: 0.90,  // Valor inicial
      synchronicityGuidance: null,
      binauralFrequency: 10.0,  // Frequência inicial (alfa)
      arVisualizationEnabled: true,
      collectiveCoherence: 0.0,
      sessionStatus: 'active',
    };

    this.activeSessions.set(sessionId, session);

    console.log(`🌠🌀🧘 Sessão de meditação iniciada: ${sessionId} (Ω alvo=${targetOmega}, ${participants.length} participantes)`);

    return session;
  }

  /**
   * Processa padrão de sincronicidade para guiar meditação
   */
  handleSynchronicityForMeditation(sessionId: string, pattern: SynchronicityPattern): void {
    const session = this.activeSessions.get(sessionId);
    if (!session || session.sessionStatus !== 'active') {return;}

    // Verificar se padrão é relevante para a sessão
    if (pattern.significanceScore < this.config.synchronicitySensitivity) {
      return;
    }

    // Atualizar orientação da sessão com padrão de sincronicidade
    session.synchronicityGuidance = pattern;

    // Ajustar frequência de binaural beats baseado no padrão
    this.adjustBinauralFrequency(session, pattern);

    console.log(`🌀 Padrão de sincronicidade aplicado à sessão ${sessionId}: ${pattern.patternType} (significância=${pattern.significanceScore.toFixed(3)})`);
  }

  /**
   * Ajusta frequência de binaural beats baseado em padrão de sincronicidade
   */
  private adjustBinauralFrequency(session: MeditationSession, pattern: SynchronicityPattern): void {
    // Mapear tipo de padrão para faixa de frequência
    const frequencyMap: Record<string, [number, number]> = {
      meaningful_coincidence: [8.0, 12.0],   // Alfa: relaxamento focado
      acausal_cluster: [4.0, 8.0],           // Theta: meditação profunda
      retrocausal_echo: [0.5, 4.0],          // Delta: sono/cura
      ethical_resonance: [12.0, 30.0],       // Beta/gama: insight/criatividade
    };

    const [minFreq, maxFreq] = frequencyMap[pattern.patternType] || [10.0, 12.0];

    // Calcular frequência alvo baseada na significância do padrão
    const significanceFactor = (pattern.significanceScore - 0.6) / 0.4;  // Normalizar para 0-1
    const targetFrequency = minFreq + significanceFactor * (maxFreq - minFreq);

    // Suavizar transição para nova frequência
    session.binauralFrequency += (targetFrequency - session.binauralFrequency) * this.config.binauralAdaptationRate;

    // Limitar faixa válida
    session.binauralFrequency = Math.max(0.5, Math.min(40.0, session.binauralFrequency));
  }

  /**
   * Atualiza biofeedback de participante e recalcula coerência coletiva
   */
  async updateParticipantBiofeedback(participantId: string, biofeedback: Omit<ParticipantBiofeedback, 'participantId' | 'timestamp_ns'>): Promise<void> {
    const feedback: ParticipantBiofeedback = {
      ...biofeedback,
      participantId,
      timestamp_ns: Date.now() * 1e6,
    };

    this.participantBiofeedback.set(participantId, feedback);

    // Recalcular coerência coletiva para sessões ativas
    for (const [sessionId, session] of this.activeSessions) {
      if (session.participants.includes(participantId) && session.sessionStatus === 'active') {
        await this.updateCollectiveCoherence(sessionId);
      }
    }
  }

  /**
   * Recalcula coerência coletiva para uma sessão
   */
  private async updateCollectiveCoherence(sessionId: string): Promise<void> {
    const session = this.activeSessions.get(sessionId);
    if (!session) {return;}

    // Coletar biofeedback dos participantes da sessão
    const participantFeedback = session.participants
      .map(pid => this.participantBiofeedback.get(pid))
      .filter((fb): fb is ParticipantBiofeedback => fb !== undefined);

    if (participantFeedback.length === 0) {return;}

    // Calcular coerência coletiva como média ponderada
    const weights = { heartRate: 0.2, gsr: 0.2, alpha: 0.3, theta: 0.3 };

    let collectiveScore = 0;
    for (const fb of participantFeedback) {
      const personalCoherence = (
        weights.heartRate * (1 - Math.abs(fb.heartRate - 72) / 40) +  // Ideal: 72 BPM
        weights.gsr * fb.gsr +
        weights.alpha * fb.brainwaveAlpha +
        weights.theta * fb.brainwaveTheta
      );
      collectiveScore += personalCoherence * fb.coherenceScore;
    }

    session.collectiveCoherence = Math.min(1.0, collectiveScore / participantFeedback.length);

    // Atualizar Ω coletivo baseado em coerência
    const [minOmega, maxOmega] = this.config.targetOmegaRange;
    session.currentOmega = minOmega + (maxOmega - minOmega) * session.collectiveCoherence;

    // Verificar se threshold de coerência coletiva foi alcançado
    if (session.collectiveCoherence >= this.config.collectiveThreshold) {
      this.triggerCollectiveAchievement(session);
    }
  }

  /**
   * Dispara evento de conquista coletiva quando coerência threshold é alcançada
   */
  private triggerCollectiveAchievement(session: MeditationSession): void {
    console.log(`✨ Coerência coletiva alcançada na sessão ${session.sessionId}: ${session.collectiveCoherence.toFixed(3)} (Ω=${session.currentOmega.toFixed(3)})`);
  }

  /**
   * Finaliza sessão de meditação
   */
  async endMeditationSession(sessionId: string): Promise<void> {
    const session = this.activeSessions.get(sessionId);
    if (!session) {return;}

    session.sessionStatus = 'completed';

    console.log(`✅ Sessão de meditação concluída: ${sessionId} (duração=${((Date.now() * 1e6 - session.startTime_ns) / 1e6).toFixed(1)}ms)`);
  }

  /**
   * Consulta sessão ativa por ID
   */
  getSession(sessionId: string): MeditationSession | undefined {
    return this.activeSessions.get(sessionId);
  }

  /**
   * Dashboard de métricas de meditação coerente
   */
  getMeditationDashboard() {
    const activeSessions = Array.from(this.activeSessions.values())
      .filter(s => s.sessionStatus === 'active');

    return {
      activeSessionsCount: activeSessions.length,
      totalParticipants: activeSessions.reduce((sum, s) => sum + s.participants.length, 0),
      avgCollectiveCoherence: activeSessions.length > 0
        ? activeSessions.reduce((sum, s) => sum + s.collectiveCoherence, 0) / activeSessions.length
        : 0,
      avgCurrentOmega: activeSessions.length > 0
        ? activeSessions.reduce((sum, s) => sum + s.currentOmega, 0) / activeSessions.length
        : 0,
      sessionsWithSynchronicityGuidance: activeSessions.filter(s => s.synchronicityGuidance).length,
      binauralFrequencyRange: activeSessions.length > 0
        ? {
            min: Math.min(...activeSessions.map(s => s.binauralFrequency)),
            max: Math.max(...activeSessions.map(s => s.binauralFrequency)),
          }
        : null,
      recentBiofeedback: Array.from(this.participantBiofeedback.values()).slice(-10),
    };
  }
}

// Instância global
export const coherentMeditationEngine = new CoherentMeditationEngine();
