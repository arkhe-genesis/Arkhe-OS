/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export interface SessionEvent {
  type: 'click' | 'navigation' | 'error' | 'rage_click' | 'performance';
  timestamp: number;
  target?: string;
  metadata?: Record<string, unknown>;
}

export interface HydroContext {
  nodeId: string;
  waterLevel: number;        // metros
  coherence: number;         // T ≈ 1 (0-1)
  massBalanceValid: boolean; // ZK proof status
  geofenceStatus: 'SAFE' | 'WARNING' | 'CRITICAL';
}

export class LucentCollector {
  private ws: WebSocket;
  private sessionId: string;
  private eprContext: { getNonce: () => string }; // EPRHandshake;
  public hydroContext: HydroContext;
  private eventBuffer: SessionEvent[] = [];
  private flush_interval_id: ReturnType<typeof setInterval> | null = null;

  constructor(
    apiUrl: string,
    sessionId: string,
    hydroNodeId: string,
    private options: {
      anonymize?: boolean;
      zkProof?: boolean;
      correlateHydro?: boolean;
      flushInterval?: number;
    } = {}
  ) {
    this.sessionId = sessionId;
    this.hydroContext = { nodeId: hydroNodeId } as HydroContext;

    // Handshake quântico EPR
    this.eprContext = { getNonce: () => Math.random().toString() }; // new EPRHandshake();

    // Conexão qhttp (quantum WebSocket)
    this.ws = new (globalThis as unknown as { WebSocket: new (url: string) => WebSocket }).WebSocket(`quantum://${apiUrl}/lucent/session`);
    this.setupWebSocket();

    // Flush periódico
    if (this.options.flushInterval !== 0) {
        this.flush_interval_id = setInterval(() => this.flush(), this.options.flushInterval || 5000);
    }

    // Observar contexto hídrico em tempo real
    if (options.correlateHydro) {
      this.subscribeHydroContext(hydroNodeId);
    }
  }

  private setupWebSocket() {
    this.ws.onopen = () => {
      // Envia SESSION_START com EPR nonce
      const frame = {
        type: 0x20, // SESSION_START
        sessionId: this.sessionId,
        eprNonce: this.eprContext.getNonce(),
        hydroNodeId: this.hydroContext.nodeId,
        timestamp: Date.now(),
        userAgent: (globalThis as unknown as { navigator?: { userAgent: string } }).navigator?.userAgent || "mock",
        viewport: { width: 1024, height: 768 }
      };
      this.ws.send(JSON.stringify(frame));
    };
  }

  private subscribeHydroContext(nodeId: string) {
    // Conecta ao nó HYDRO-Ω para receber métricas em tempo real
    const hydroWs = new (globalThis as unknown as { WebSocket: new (url: string) => WebSocket }).WebSocket(`quantum://${apiUrl}/hydro.arkhe/node/${nodeId}`);
    hydroWs.onmessage = (event: MessageEvent) => {
      const data = JSON.parse(event.data);
      this.hydroContext = {
        nodeId: data.nodeId,
        waterLevel: data.waterLevel,
        coherence: data.coherence,
        massBalanceValid: data.zkStatus === 'verified',
        geofenceStatus: this.calculateGeofenceStatus(data.waterLevel)
      };
    };
  }

  private calculateGeofenceStatus(level: number): 'SAFE' | 'WARNING' | 'CRITICAL' {
    if (level < 10) {return 'CRITICAL';}
    if (level > 100) {return 'WARNING';}
    return 'SAFE';
  }

  // Método principal: trackeia evento
  track(event: SessionEvent): void {
    // Calcula "UX Stress" localmente
    const stressScore = this.calculateUXStress(event);

    // Correlaciona com stress hídrico se disponível
    const correlation = this.options.correlateHydro ?
      this.calculateCorrelation(stressScore, this.hydroContext) : 0;

    const enrichedEvent = {
      ...event,
      _lucent: {
        uxStress: stressScore,
        hydroContext: this.options.anonymize ? undefined : this.hydroContext,
        correlationIndex: correlation,
        zkProof: this.options.zkProof ? this.generateZKProof(event) : undefined
      }
    };

    this.eventBuffer.push(enrichedEvent as unknown as SessionEvent);

    // Rage click detection (imediato)
    if (event.type === 'rage_click' && correlation > 0.8) {
      this.emitQuantumAlert('SINCRONICIDADE_ALTA', { stressScore, correlation });
    }
  }

  private calculateUXStress(event: SessionEvent): number {
    let score = 0;
    if (event.type === 'error') {score += 0.4;}
    if (event.type === 'rage_click') {score += 0.6;}
    if (event.type === 'performance' && event.metadata && (event.metadata.loadTime as number) > 3000) {score += 0.3;}

    // Normaliza 0-1
    return Math.min(1, score);
  }

  private calculateCorrelation(uxStress: number, hydro: HydroContext): number {
    // Algoritmo de correlação quântica
    // Se UX está estressado (erros) E aquífero está estressado (baixo nível),
    // há uma "sincronicidade" que pode indicar ataque ou anomalia sistêmica

    const hydroStress = 1 - (hydro.waterLevel / 100); // 0 = cheio, 1 = vazio
    const coherencePenalty = 1 - hydro.coherence;     // Se decoerente, reduz correlação

    const rawCorrelation = (uxStress * hydroStress) * (1 - coherencePenalty);

    // Só reporta correlação se ambos os sistemas estão coerentes
    return hydro.massBalanceValid ? rawCorrelation : 0;
  }

  private generateZKProof(_event: SessionEvent): string {
    return "0x" + Math.random().toString(16).substring(2);
  }

  private emitQuantumAlert(type: string, data: unknown) {
    const alert = {
      type: 0x23, // SESSION_ANALYSIS
      alertType: type,
      sessionId: this.sessionId,
      hydroNodeId: this.hydroContext.nodeId,
      timestamp: Date.now(),
      severity: 'HIGH',
      data
    };
    this.ws.send(JSON.stringify(alert));
  }

  private flush(): void {
    if (this.eventBuffer.length === 0) {return;}

    const batch = {
      type: 0x21, // SESSION_EVENT batch
      sessionId: this.sessionId,
      events: this.eventBuffer,
      hydroSnapshot: this.hydroContext,
      coherence: this.hydroContext?.coherence || 0,
      timestamp: Date.now()
    };

    this.ws.send(JSON.stringify(batch));
    this.eventBuffer = [];
  }

  // Método específico para erros
  error(error: Error, context?: unknown): void {
    this.track({
      type: 'error',
      timestamp: Date.now(),
      metadata: {
        message: error.message,
        stack: this.options.anonymize ? undefined : error.stack,
        context
      }
    });
  }

  // Finaliza sessão
  end(): void {
    if (this.flush_interval_id) {clearInterval(this.flush_interval_id);}
    const frame = {
      type: 0x22, // SESSION_END
      sessionId: this.sessionId,
      duration: Date.now() - this.startTime,
      finalHydroContext: this.hydroContext
    };
    this.ws.send(JSON.stringify(frame));
    this.ws.close();
  }

  private startTime = Date.now();
}

// Exporta para uso no browser
export default LucentCollector;
