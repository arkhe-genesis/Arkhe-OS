const crypto = require('crypto');

/**
 * TemporalChainLogger — Registra sinais Telegraph como blocos Θ
 *
 * Acoplado ao barramento Telegraph, intercepta o método publish
 * e cunha um bloco Θ para cada sinal. A cadeia é mantida em
 * memória (volátil — ver WARNING 803 v2.0 para persistência real).
 */
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
    this.telegraph.publish = (signalData) => {
      const signal = signalData instanceof require('./telegraph').Signal
        ? signalData
        : new (require('./telegraph').Signal)(signalData);

      const block = {
        index: this.chain.length,
        timestamp: new Date().toISOString(),
        topic: signal.topic,
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
      console.log(`[TEMPORAL] Θ-${block.index} | ${signal.topic} | ${signal.metric}=${signal.value}`);
      return originalPublish(signalData);
    };
  }

  getChain() { return this.chain; }
  getLastBlock() { return this.chain[this.chain.length - 1] || null; }

  verifyChain() {
    for (let i = 1; i < this.chain.length; i++) {
      if (this.chain[i].previous_hash !== this.chain[i-1].hash) return false;
      // Verify block hash
      const block = { ...this.chain[i] };
      delete block.hash;
      const expected = crypto.createHash('sha3-256')
        .update(JSON.stringify(block))
        .digest('hex');
      if (expected !== this.chain[i].hash) return false;
    }
    return true;
  }
}

module.exports = TemporalChainLogger;