// ═══════════════════════════════════════════════════════════════════
// ARKHE TEMPORAL‑CHAIN LOGGER — Persiste sinais como blocos Θ
// ═══════════════════════════════════════════════════════════════════

const crypto = require('crypto');

class TemporalChainLogger {
  constructor(telegraph) {
    this.telegraph = telegraph;
    this.chain = [];                     // registro imutável em memória
    this.lastBlock = null;
    this._init();
  }

  _init() {
    // Intercepta o método publish do Telegraph para registrar na chain
    const originalPublish = this.telegraph.publish.bind(this.telegraph);
    this.telegraph.publish = (topic, signal, config = { enableZK: true }) => {
      const block = {
        index: this.chain.length,
        timestamp: new Date().toISOString(),
        topic,
        signal: {
          source: signal.source,
          metric: signal.metric,
          value: signal.value,
          unit: signal.unit,
          seal: signal.seal,
        },
        previous_hash: this.lastBlock || '0',
        hash: null,
      };
      block.hash = crypto.createHash('sha3-256')
        .update(JSON.stringify(block))
        .digest('hex');
      this.chain.push(block);
      this.lastBlock = block.hash;
      console.log(`[TEMPORAL] Θ‑${block.index} | ${topic} | ${signal.metric}=${signal.value}`);
      return originalPublish(topic, signal, config);
    };
  }

  getChain() { return this.chain; }
  getLastBlock() { return this.chain[this.chain.length - 1] || null; }
  verifyChain() {
    for (let i = 1; i < this.chain.length; i++) {
      if (this.chain[i].previous_hash !== this.chain[i-1].hash) return false;
    }
    return true;
  }
}

module.exports = TemporalChainLogger;