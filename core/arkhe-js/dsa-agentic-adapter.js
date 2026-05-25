// ═══════════════════════════════════════════════════════════════════
// ARKHE DSA ↔ AGENTIC ADAPTER — Interface para agentes autônomos
// ═══════════════════════════════════════════════════════════════════

class DSAAgenticAdapter {
  constructor(dsaTracker, telegraph) {
    this.dsa = dsaTracker;
    this.telegraph = telegraph;
  }

  handleQuery(msg) {
    const { pattern, problem } = msg;
    if (pattern && problem) {
      const result = this.dsa.solve(pattern, problem);
      if (result.alert) {
        // Emitir alerta de template pronto
        this.telegraph.publish('/coherence/dsa', {
          metric: 'template_ready',
          value: result.coherence,
          unit: 'alert',
        });
      }
      return result;
    } else if (msg.command === 'phi') {
      return { rDSA: this.dsa.orderParameter() };
    }
    return { error: 'Parâmetros inválidos' };
  }

  // Registra handlers de tópicos de agentes
  listen() {
    // O agente publica em /agent/query/dsa, o adaptador responde em /agent/response/dsa
    // Isso é tratado pelo próprio Telegraph via subscribe
    if (this.telegraph) {
      const ws = { readyState: 1, send: (data) => console.log('[AGENT] Resposta:', data) }; // placeholder real
      this.telegraph.subscribe(ws, '/agent/query/dsa');
      // Na implementação real, o Telegraph chamaria handleQuery ao receber mensagens
    }
  }
}

module.exports = DSAAgenticAdapter;
