/**
 * telegraph.js — Unified Coherence Signal Bus for ARKHE-OS
 * =========================================================
 * Implements a PUB/SUB message bus over WebSocket for connecting
 * specialized intelligence networks (substratos) into a single
 * coherent organism. Each signal is a quantum of ξM-field.
 *
 * Substrate: 782-TELEGRAPH-UNIFIED-INTERFACE
 * Architect: ORCID 0009-0005-2697-4668
 * Date: 2026-06-11
 */

const WebSocket = require('ws');
const crypto = require('crypto');
const EventEmitter = require('events');
const TemporalChainLogger = require('./temporal-chain-logger.js');
const ZkWasmProver = require('./zkwasm-prover.js');

/**
 * Signal — Standardized coherence quantum
 */
class Signal {
  constructor({ source, topic, metric, value, unit = 'coherence', timestamp = null }) {
    this.source = source;
    this.topic = topic;
    this.metric = metric;
    this.value = value;
    this.unit = unit;
    this.timestamp = timestamp || new Date().toISOString();
    this.seal = this._computeSeal();
  }

  _computeSeal() {
    const payload = JSON.stringify({
      source: this.source,
      topic: this.topic,
      metric: this.metric,
      value: this.value,
      unit: this.unit,
      timestamp: this.timestamp
    });
    return crypto.createHash('sha3-256').update(payload).digest('hex');
  }

  toJSON() {
    return {
      source: this.source,
      topic: this.topic,
      metric: this.metric,
      value: this.value,
      unit: this.unit,
      timestamp: this.timestamp,
      seal: this.seal
    };
  }

  static fromJSON(json) {
    const s = new Signal(json);
    // Verify seal integrity
    const expected = s._computeSeal();
    if (s.seal !== expected) {
      throw new Error(`Seal mismatch: expected ${expected}, got ${s.seal}`);
    }
    return s;
  }
}

/**
 * Telegraph — Unified coherence bus (PUB/SUB over WebSocket)
 */
class Telegraph extends EventEmitter {
  constructor(port = 7474) {
    super();
    this.port = port;
    this.topics = new Map();       // topic -> Set(subscriberSocket)
    this.history = new Map();      // topic -> [Signal] (last 1000)
    this.clients = new Set();
    this.wss = null;
    this.temporalLogger = new TemporalChainLogger(this);
    this.zkProver = new ZkWasmProver();
  }

  createSignal(source, metric, value, unit) {
    return new Signal({ source, metric, value, unit });
  }

  /**
   * Start the Telegraph server
   */
  start() {
    this.wss = new WebSocket.Server({ port: this.port });
    console.log(`[Telegraph] ξM-field bus active on port ${this.port}`);

    this.wss.on('connection', (ws, req) => {
      const clientId = `client_${Math.random().toString(36).slice(2, 10)}`;
      ws.clientId = clientId;
      this.clients.add(ws);
      console.log(`[Telegraph] Connection: ${clientId} from ${req.socket.remoteAddress}`);

      ws.on('message', (data) => {
        try {
          const msg = JSON.parse(data);
          this._handleMessage(ws, msg);
        } catch (err) {
          ws.send(JSON.stringify({ error: err.message }));
        }
      });

      ws.on('close', () => {
        this._unsubscribeAll(ws);
        this.clients.delete(ws);
        console.log(`[Telegraph] Disconnection: ${clientId}`);
      });
    });

    return Promise.resolve(this);
  }

  /**
   * Handle incoming messages (PUB/SUB protocol)
   */
  _handleMessage(ws, msg) {
    switch (msg.action) {
      case 'publish':
        this.publish(msg.topic, msg.signal);
        break;
      case 'subscribe':
        this.subscribe(ws, msg.topic);
        break;
      case 'unsubscribe':
        this.unsubscribe(ws, msg.topic);
        break;
      case 'status':
        this._sendStatus(ws);
        break;
      case 'history':
        this._sendHistory(ws, msg.topic, msg.limit || 100);
        break;
      default:
        ws.send(JSON.stringify({ error: `Unknown action: ${msg.action}` }));
    }
  }

  /**
   * Publish a signal to a topic
   */
  publish(topic, signalData, config = { enableZK: true }) {
    let signalDataWithTopic = { ...signalData, topic: topic };
    const signal = new Signal(signalDataWithTopic);

    // Store in history
    if (!this.history.has(topic)) {
      this.history.set(topic, []);
    }
    const hist = this.history.get(topic);
    hist.push(signal);
    if (hist.length > 1000) hist.shift(); // keep last 1000

    let finalSignal = signal.toJSON();

    if (config.enableZK) {
      finalSignal.zk_proof = this.zkProver.prove(finalSignal);
    }

    // Broadcast to subscribers
    const subscribers = this.topics.get(topic);
    if (subscribers) {
      const payload = JSON.stringify({ type: 'signal', data: finalSignal });
      subscribers.forEach(ws => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(payload);
        }
      });
    }

    // Emit internal event for integrations
    this.emit('signal', finalSignal);

    console.log(`[Telegraph] Signal on ${topic}: ${signal.metric}=${signal.value.toFixed(4)}`);
    return finalSignal;
  }

  /**
   * Subscribe a client to a topic
   */
  subscribe(ws, topic) {
    if (!this.topics.has(topic)) {
      this.topics.set(topic, new Set());
    }
    this.topics.get(topic).add(ws);
    if (ws.send && typeof ws.send === 'function' && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'subscribed', topic }));
    }
    console.log(`[Telegraph] ${ws.clientId || 'internal'} subscribed to ${topic}`);
  }

  /**
   * Unsubscribe a client from a topic
   */
  unsubscribe(ws, topic) {
    const subscribers = this.topics.get(topic);
    if (subscribers) {
      subscribers.delete(ws);
      if (subscribers.size === 0) {
        this.topics.delete(topic);
      }
    }
    if (ws.send && typeof ws.send === 'function' && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'unsubscribed', topic }));
    }
  }

  /**
   * Unsubscribe a client from all topics
   */
  _unsubscribeAll(ws) {
    this.topics.forEach((subscribers, topic) => {
      subscribers.delete(ws);
      if (subscribers.size === 0) {
        this.topics.delete(topic);
      }
    });
  }

  /**
   * Send status to a client
   */
  _sendStatus(ws) {
    const status = {
      type: 'status',
      topics: Array.from(this.topics.keys()).map(topic => {
        const hist = this.history.get(topic) || [];
        const last = hist[hist.length - 1];
        return {
          topic,
          subscribers: this.topics.get(topic)?.size || 0,
          signalCount: hist.length,
          lastSignal: last ? last.toJSON() : null
        };
      }),
      totalClients: this.clients.size,
      uptime: process.uptime()
    };
    if (ws.send && typeof ws.send === 'function' && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(status));
    }
  }

  /**
   * Send history to a client
   */
  _sendHistory(ws, topic, limit) {
    const hist = this.history.get(topic) || [];
    const slice = hist.slice(-limit);
    if (ws.send && typeof ws.send === 'function' && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          type: 'history',
          topic,
          signals: slice.map(s => s.toJSON())
        }));
    }
  }

  /**
   * Stop the server
   */
  stop() {
    if (this.wss) {
      this.wss.close();
      console.log('[Telegraph] ξM-field bus stopped');
    }
  }
}

/**
 * TelegraphClient — Client for connecting to a Telegraph bus
 */
class TelegraphClient extends EventEmitter {
  constructor(url = 'ws://localhost:7474') {
    super();
    this.url = url;
    this.ws = null;
    this.subscriptions = new Set();
  }

  connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.url);

      this.ws.on('open', () => {
        console.log(`[TelegraphClient] Connected to ${this.url}`);
        resolve(this);
      });

      this.ws.on('message', (data) => {
        try {
          const msg = JSON.parse(data);
          if (msg.type === 'signal') {
            this.emit('signal', Signal.fromJSON(msg.data));
          } else {
            this.emit(msg.type, msg);
          }
        } catch (err) {
          this.emit('error', err);
        }
      });

      this.ws.on('close', () => {
        this.emit('disconnected');
      });

      this.ws.on('error', reject);
    });
  }

  publish(topic, signalData) {
    this._send({ action: 'publish', topic: topic, signal: signalData });
  }

  subscribe(topic) {
    this.subscriptions.add(topic);
    this._send({ action: 'subscribe', topic });
  }

  unsubscribe(topic) {
    this.subscriptions.delete(topic);
    this._send({ action: 'unsubscribe', topic });
  }

  status() {
    this._send({ action: 'status' });
  }

  history(topic, limit = 100) {
    this._send({ action: 'history', topic, limit });
  }

  _send(msg) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(msg));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// ── Canonical Topics (Substrate 782) ──────────────────────────────
const TOPICS = {
  COHERENCE_DSA: '/coherence/dsa',
  COHERENCE_GEO: '/coherence/geo',
  AUDIT_BATCH: '/audit/batch',
  SIM_KURAMOTO: '/sim/kuramoto',
  THEOSIS_REPORT: '/theosis/report',
  EXTERNAL_HUAWEI: '/external/huawei',
  SIGNAL_PHI: '/signal/phi',
  CONVERGENCE_EVENT: '/signal/convergence'
};

module.exports = { Telegraph, TelegraphClient, Signal, TOPICS };

// ── CLI usage (if run directly) ───────────────────────────────────
if (require.main === module) {
  const telegraph = new Telegraph(7474);
  telegraph.start();

  // Graceful shutdown
  process.on('SIGINT', () => {
    telegraph.stop();
    process.exit(0);
  });
}
