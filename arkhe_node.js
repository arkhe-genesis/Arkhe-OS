#!/usr/bin/env node

/**
 * ARKHE Ω‑TEMP v4.5.0 — Node.js Core Implementation
 * =================================================================
 * Substrates implemented:
 *   5021  TimeCrystal
 *   333   AuditLedger (in‑memory, SHA3‑256 verified)
 *   5033  TemporalHashChain
 *   5034  ConsistencyOracle
 *   5035  CausalShield
 *   5036  RetrocausalValidator
 *   6041  Partial‑Order Routing (simple table)
 *
 * Usage:
 *   node arkhe_node.js
 *
 * The script runs a brief demonstration of retrocausal message validation,
 * chain insertion, and router operation.
 */

const crypto = require('crypto');
const { EventEmitter } = require('events');

// ─────────────────────────────────────────────────────────────────────────
// CONSTANTS
// ─────────────────────────────────────────────────────────────────────────
const DEFAULT_WINDOW_SECONDS = 5 * 365.25 * 24 * 3600; // 5 anos
const QUANTUM_NEGATIVE_WINDOW_SECONDS = 1e-12;         // 1 picosegundo
const PLANCK_HBAR = 1.054571817e-34;

// ─────────────────────────────────────────────────────────────────────────
// SUBSTRATE 5021 — TIME CRYSTAL
// ─────────────────────────────────────────────────────────────────────────
class TimeCrystal {
  constructor(frequencyKhz = 465.0) {
    this.omegaHz = frequencyKhz * 1000.0;
    this.start = process.hrtime.bigint();
  }

  phase() {
    const now = process.hrtime.bigint();
    const deltaSec = Number(now - this.start) / 1e9;
    return (this.omegaHz * deltaSec) % (2 * Math.PI);
  }

  isAligned(tolerance = 1e-6) {
    const p = this.phase();
    return Math.min(p, 2 * Math.PI - p) < tolerance;
  }
}

// ─────────────────────────────────────────────────────────────────────────
// SUBSTRATE 333 — AUDIT LEDGER (in‑memory, SHA3‑256 integrity)
// ─────────────────────────────────────────────────────────────────────────
class AuditLedger {
  constructor() {
    this.entries = [];
    this.nextId = 1;
  }

  static sha3_256(data) {
    return crypto.createHash('sha3-256').update(data).digest('hex');
  }

  record(eventType, payload) {
    const payloadStr = typeof payload === 'string' ? payload : JSON.stringify(payload);
    const hash = AuditLedger.sha3_256(payloadStr);
    const entry = {
      id: this.nextId++,
      type: eventType,
      payload: payload,
      timestamp: Date.now() / 1000,
      hash: hash
    };
    this.entries.push(entry);
    return hash;
  }

  getRecords(limit = 500, offset = 0) {
    const start = Math.max(0, this.entries.length - offset - limit);
    const end = this.entries.length - offset;
    return this.entries.slice(start, end);
  }

  count() {
    return this.entries.length;
  }

  verifyIntegrity() {
    for (const entry of this.entries) {
      const payloadStr = typeof entry.payload === 'string' ? entry.payload : JSON.stringify(entry.payload);
      if (AuditLedger.sha3_256(payloadStr) !== entry.hash) {
        return false;
      }
    }
    return true;
  }
}

// ─────────────────────────────────────────────────────────────────────────
// TEMPORAL MESSAGE
// ─────────────────────────────────────────────────────────────────────────
class TemporalMessage {
  constructor(id, content, sourceTimestamp, targetTimestamp, senderSeal, receiverSeal) {
    this.id = id;
    this.content = content;
    this.sourceTimestamp = sourceTimestamp;
    this.targetTimestamp = targetTimestamp;
    this.senderSeal = senderSeal;
    this.receiverSeal = receiverSeal;
  }
}

// ─────────────────────────────────────────────────────────────────────────
// CONSISTENCY REPORT
// ─────────────────────────────────────────────────────────────────────────
class ConsistencyReport {
  constructor() {
    this.consistent = false;
    this.score = 0.0;
    this.checks = {};
    this.violations = [];
    this.paradoxType = null;
    this.quantumCoherent = false;
  }
}

// ─────────────────────────────────────────────────────────────────────────
// SUBSTRATE 5034 — TEMPORAL CONSISTENCY ORACLE
// ─────────────────────────────────────────────────────────────────────────
class TemporalConsistencyOracle {
  constructor(ledger, epsilon = 1.0) {
    this.ledger = ledger;
    this.epsilon = epsilon;
  }

  evaluate(msg, zkProof = null) {
    const report = new ConsistencyReport();
    const delta = msg.targetTimestamp - msg.sourceTimestamp;
    report.quantumCoherent = this._isQuantumNegativeTime(delta);

    const [hScore, hViol] = this._checkHarmlessness(msg);
    const [pScore, pViol] = this._checkParadoxFree(msg);
    const [eScore, eViol] = this._checkEntropySafe(msg);
    const [cScore, cViol] = this._checkCoherent(msg);
    const [zScore, zViol] = this._checkZkValid(msg, zkProof);

    report.checks = {
      harmless: hScore,
      paradoxFree: pScore,
      entropySafe: eScore,
      coherent: cScore,
      zkValid: zScore
    };
    report.violations = [...hViol, ...pViol, ...eViol, ...cViol, ...zViol];

    let score = Math.min(hScore, pScore, eScore, cScore, zScore);
    if (report.quantumCoherent) {
      score = Math.min(1.0, score + 0.05);
      report.checks.quantumTime = score;
    }

    report.score = Math.round(score * 1e6) / 1e6;
    report.consistent = report.score >= 0.999;
    if (!report.consistent && report.violations.length > 0) {
      report.paradoxType = this._classify(report.violations);
    }
    return report;
  }

  _isQuantumNegativeTime(delta) {
    return delta < 0 && Math.abs(delta) <= QUANTUM_NEGATIVE_WINDOW_SECONDS;
  }

  _checkHarmlessness(msg) {
    // simplified: no duplicate semantic check
    return [1.0, []];
  }

  _checkParadoxFree(msg) {
    const delta = msg.targetTimestamp - msg.sourceTimestamp;
    if (this._isQuantumNegativeTime(delta)) {
      return [1.0, []];
    }
    if (delta < 0) {
      return [0.0, ["Paradox detected: negative time jump outside quantum window"]];
    }
    // simplified: no causal loop detection
    return [1.0, []];
  }

  _checkEntropySafe(msg) {
    const dt = Math.abs(msg.targetTimestamp - msg.sourceTimestamp);
    const ent = msg.content.length * 8;
    const temporalCost = Math.min(1.0, dt / DEFAULT_WINDOW_SECONDS);
    const entropyCost = Math.min(1.0, ent / (1024 * 1024 * 8));
    const score = Math.max(0.0, 1.0 - 0.5 * temporalCost - 0.5 * entropyCost);
    const violations = [];
    if (temporalCost >= 1.0) violations.push("Temporal jump near limit");
    return [score, violations];
  }

  _checkCoherent(msg) {
    const dt = msg.targetTimestamp - msg.sourceTimestamp;
    const mw = DEFAULT_WINDOW_SECONDS;
    if (Math.abs(dt) > mw) {
      return [Math.max(0.0, 1.0 - Math.abs(dt) / (mw * 10)), ["Jump exceeds 5 years"]];
    }
    return [1.0 - (Math.abs(dt) / mw) * 0.1, []];
  }

  _checkZkValid(msg, zkProof) {
    if (!zkProof) return [0.5, ["No ZK proof"]];
    return [1.0, []];
  }

  _classify(violations) {
    const text = violations.join(' ').toLowerCase();
    if (text.includes('causal') || text.includes('loop')) return "GRANDPARENT";
    if (text.includes('entrop')) return "ENTROPY";
    if (text.includes('paradox')) return "PARADOX";
    return null;
  }
}

// ─────────────────────────────────────────────────────────────────────────
// SUBSTRATE 5035 — CAUSAL SHIELD
// ─────────────────────────────────────────────────────────────────────────
class CausalShield {
  constructor(ledger) {
    this.ledger = ledger;
    this.whitelist = new Set();
    this.blacklist = new Set();
  }

  evaluate(msg) {
    const now = Date.now() / 1000;
    const delta = msg.targetTimestamp - now;
    const isQuantum = delta < 0 && Math.abs(delta) <= QUANTUM_NEGATIVE_WINDOW_SECONDS;
    if (!isQuantum) {
      if (Math.abs(delta) > DEFAULT_WINDOW_SECONDS) {
        return { ok: false, reason: "Timestamp outside 5-year window" };
      }
      // rate‑limit simplified
    }
    return { ok: true, reason: "OK" };
  }

  whitelistSeal(seal) { this.whitelist.add(seal); }
  blacklistSeal(seal) { this.blacklist.add(seal); }
}

// ─────────────────────────────────────────────────────────────────────────
// SUBSTRATE 5036 — RETROCAUSAL VALIDATOR
// ─────────────────────────────────────────────────────────────────────────
class RetrocausalValidator {
  constructor(ledger) {
    this.shield = new CausalShield(ledger);
    this.oracle = new TemporalConsistencyOracle(ledger);
    this.accepted = 0;
    this.rejected = 0;
  }

  validate(msg, zkProof = null) {
    const { ok, reason } = this.shield.evaluate(msg);
    if (!ok) {
      this.rejected++;
      return { accepted: false, score: 0.0, report: null, shieldPassed: false, shieldReason: reason };
    }
    const report = this.oracle.evaluate(msg, zkProof);
    if (report.consistent) {
      this.accepted++;
    } else {
      this.rejected++;
    }
    return {
      accepted: report.consistent,
      score: report.score,
      report: report,
      shieldPassed: true,
      shieldReason: reason
    };
  }

  stats() {
    const total = this.accepted + this.rejected;
    return {
      accepted: this.accepted,
      rejected: this.rejected,
      total: total,
      rate: total ? `${(this.accepted / total * 100).toFixed(1)}%` : "0%"
    };
  }
}

// ─────────────────────────────────────────────────────────────────────────
// SUBSTRATE 5033 — TEMPORAL HASH CHAIN
// ─────────────────────────────────────────────────────────────────────────
class TemporalBlock {
  constructor(index, targetTs, prevHash, dataHash, proof, depth) {
    this.index = index;
    this.targetTs = targetTs;
    this.prevHash = prevHash;
    this.dataHash = dataHash;
    this.proof = proof;
    this.depth = depth;
    this.blockHash = this.computeHash();
  }

  computeHash() {
    const raw = `${this.index}|${this.targetTs}|${this.prevHash}|${this.dataHash}|${this.proof}|${this.depth}`;
    return crypto.createHash('sha3-256').update(raw).digest('hex');
  }
}

class TemporalHashChain {
  constructor() {
    this.chain = [];
    this._createGenesis();
  }

  _createGenesis() {
    const genesis = new TemporalBlock(
      0, 0.0,
      '0'.repeat(64),
      crypto.createHash('sha3-256').update('ARKHE_GENESIS').digest('hex'),
      'GENESIS', 0.0
    );
    this.chain.push(genesis);
  }

  insertRetrocausal(targetTs, dataJson, proof, depth = 0.0) {
    const dataHash = crypto.createHash('sha3-256').update(dataJson).digest('hex');
    const block = new TemporalBlock(0, targetTs, '', dataHash, proof, depth);

    let idx = this.chain.length;
    for (let i = 0; i < this.chain.length; i++) {
      if (targetTs < this.chain[i].targetTs) {
        idx = i;
        break;
      }
    }
    if (idx === 0) return { block: null, error: "Cannot insert before genesis" };

    block.prevHash = this.chain[idx - 1].blockHash;
    block.index = this.chain[idx - 1].index + 1;
    block.blockHash = block.computeHash();
    this.chain.splice(idx, 0, block);

    for (let i = idx + 1; i < this.chain.length; i++) {
      this.chain[i].prevHash = this.chain[i - 1].blockHash;
      this.chain[i].index = this.chain[i - 1].index + 1;
      this.chain[i].blockHash = this.chain[i].computeHash();
    }
    return { block, error: "" };
  }

  get length() { return this.chain.length; }
  get headHash() { return this.chain[this.chain.length - 1].blockHash; }

  verifyIntegrity() {
    for (let i = 1; i < this.chain.length; i++) {
      const b = this.chain[i];
      const p = this.chain[i - 1];
      if (b.prevHash !== p.blockHash) return false;
      if (b.index !== p.index + 1) return false;
      if (b.targetTs < p.targetTs) return false;
    }
    return true;
  }
}

// ─────────────────────────────────────────────────────────────────────────
// SUBSTRATE 6041 — PARTIAL‑ORDER ROUTING TABLE (simplified)
// ─────────────────────────────────────────────────────────────────────────
class TemporalRoutingTable {
  constructor() {
    this.routes = new Map();
  }

  addRoute(dest, nextHop, cost, consistency, expires) {
    this.routes.set(dest, { nextHop, cost, consistency, expires });
  }

  bestRoute(dest) {
    const route = this.routes.get(dest);
    if (!route) return null;
    const now = Date.now() / 1000;
    if (route.expires > now) return route;
    return null;
  }

  expire() {
    const now = Date.now() / 1000;
    for (const [key, val] of this.routes) {
      if (val.expires <= now) this.routes.delete(key);
    }
  }

  allRoutes() {
    const now = Date.now() / 1000;
    const result = [];
    for (const [dest, val] of this.routes) {
      if (val.expires > now) result.push({ dest, ...val });
    }
    return result.sort((a, b) => a.cost - b.cost);
  }
}

// ─────────────────────────────────────────────────────────────────────────
// RETRO ROUTER
// ─────────────────────────────────────────────────────────────────────────
class RetroRouter extends EventEmitter {
  constructor(nodeId, ledger) {
    super();
    this.nodeId = nodeId;
    this.ledger = ledger;
    this.routingTable = new TemporalRoutingTable();
    this.validator = new RetrocausalValidator(ledger);
    this.temporalChain = new TemporalHashChain();
  }

  addRoute(dest, nextHop, cost, consistency, expires) {
    this.routingTable.addRoute(dest, nextHop, cost, consistency, expires);
  }

  route(msg) {
    const dest = msg.receiverSeal;
    if (dest === this.nodeId) return '__LOCAL__';
    const best = this.routingTable.bestRoute(dest);
    return best ? best.nextHop : null;
  }

  sendMessage(msg, zkProof = null) {
    const vr = this.validator.validate(msg, zkProof);
    if (!vr.accepted) {
      console.error(`[RetroRouter] Rejected: ${vr.shieldReason}`);
      return false;
    }
    const next = this.route(msg);
    if (next && next !== '__LOCAL__') {
      console.log(`[Router] Forwarding to ${next}`);
      this.emit('forward', { msg, nextHop: next, score: vr.score });
      return true;
    } else if (next === '__LOCAL__') {
      this.emit('deliver', { msg, score: vr.score });
      return true;
    }
    return false;
  }
}

// ─────────────────────────────────────────────────────────────────────────
// DEMO
// ─────────────────────────────────────────────────────────────────────────
function main() {
  console.log('=== ARKHE Ω‑TEMP v4.5.0 Node.js Core ===\n');

  const ledger = new AuditLedger();
  const router = new RetroRouter('ALFA-01', ledger);

  // register routes
  const now = Date.now() / 1000;
  router.addRoute('BETA-02', 'BETA-02', 1.0, 0.99, now + 3600);

  // test future message
  const futureMsg = new TemporalMessage(
    'msg-future-001', 'Ola do passado',
    now, now + 120,
    'ALFA-01', 'BETA-02'
  );
  const result = router.sendMessage(futureMsg, { valid: true });
  console.log(`Future message: ${result ? 'Accepted' : 'Rejected'}`);

  // insert into chain after successful send
  if (result) {
    router.temporalChain.insertRetrocausal(
      futureMsg.targetTimestamp,
      JSON.stringify({ id: futureMsg.id, content: futureMsg.content }),
      'manual-insert',
      Math.abs(futureMsg.targetTimestamp - now) / (365.25 * 86400)
    );
  }

  // test paradoxical message
  const paradoxMsg = new TemporalMessage(
    'msg-paradox-001', 'Ola do futuro?',
    now, now - 2,
    'ALFA-01', 'BETA-02'
  );
  const presult = router.sendMessage(paradoxMsg, { valid: true });
  console.log(`Paradox message: ${presult ? 'Accepted' : 'Rejected'}`);

  // chain status
  console.log(`\nChain length: ${router.temporalChain.length}`);
  console.log(`Head hash: ${router.temporalChain.headHash.slice(0, 16)}...`);
  console.log(`Chain integrity: ${router.temporalChain.verifyIntegrity()}`);

  console.log(`\nLedger entries: ${ledger.count()}`);
  console.log(`Ledger integrity: ${ledger.verifyIntegrity()}`);
}

main();
