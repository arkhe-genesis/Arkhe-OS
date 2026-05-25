// ═══════════════════════════════════════════════════════════════════
// ARKHE TEMPORAL-CHAIN LOGGER — Persiste sinais como blocos Θ
// Substrate: 803-TEMPORAL-ZKWASM-INTEGRATION
// Architect: ORCID 0009-0005-2697-4668
// Date: 2026-07-10
// ═══════════════════════════════════════════════════════════════════

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

/**
 * TemporalChainLogger — Registra sinais Telegraph como blocos Θ
 *
 * Acoplado ao barramento Telegraph, intercepta o método publish
 * e cunha um bloco Θ para cada sinal. A cadeia é mantida em
 * disco com snapshots.
 */
class TemporalChainLogger {
  constructor(telegraph) {
    this.telegraph = telegraph;
    this.chain = [];
    this.lastBlock = null;
    this.dbPath = path.join(__dirname, 'temporal_chain.json');
    this._init();
  }

  _init() {
    if (fs.existsSync(this.dbPath)) {
       try {
         this.chain = JSON.parse(fs.readFileSync(this.dbPath, 'utf8'));
         if (this.chain.length > 0) {
            this.lastBlock = this.chain[this.chain.length - 1].hash;
         }
       } catch (e) {
         console.warn("[TEMPORAL] Failed to load snapshot, starting fresh.");
       }
    }
    const originalPublish = this.telegraph.publish.bind(this.telegraph);
    this.telegraph.publish = (topic, signalData) => {
      const signal = signalData || {};
      const block = {
        index: this.chain.length,
        timestamp: new Date().toISOString(),
        topic: topic,
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
      console.log(`[TEMPORAL] Θ-${block.index} | ${topic} | ${signal.metric}=${signal.value}`);
      fs.writeFileSync(this.dbPath, JSON.stringify(this.chain, null, 2));
      return originalPublish(topic, signalData);
    };
  }

  getChain() { return this.chain; }
  getLastBlock() { return this.chain[this.chain.length - 1] || null; }

  verifyChain() {
    for (let i = 1; i < this.chain.length; i++) {
      if (this.chain[i].previous_hash !== this.chain[i-1].hash) return false;
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
