#!/usr/bin/env node
/**
 * ═══════════════════════════════════════════════════════════════════
 * ARKHE TELEGRAPH — Unified Coherence Bus (Hook 782.1)
 * ═══════════════════════════════════════════════════════════════════
 */

'use strict';

const { WebSocketServer } = require('ws');
const crypto = require('crypto');

/**
 * Barramento de mensagens PUB/SUB para o ecossistema ARKHE.
 * Conecta DSA Tracker, KuramotoHypergraph, BEAVER-Ω/7,
 * Theosis Committee, e entidades externas em tópicos canônicos.
 */
class Telegraph {
  constructor(arkheInstance, config = {}) {
    this.arkhe = arkheInstance;
    this.port = config.port || 7474;  // porta irmã da 7473 (Chladni)
    this.topics = new Map();          // topic → Set<client>
    this.lastValues = new Map();      // topic → último Signal
    this.externalKeys = new Map();    // apiKey → permissions
    this.wss = null;
    this.metrics = {
      messagesPublished: 0,
      messagesDelivered: 0,
      topicsActive: 0,
      clientsConnected: 0,
    };

    this._initTopics();
  }

  _initTopics() {
    const canonicalTopics = [
      '/coherence/dsa',
      '/coherence/geo',
      '/coherence/kuramoto',
      '/coherence/interop',
      '/audit/batch',
      '/sim/kuramoto',
      '/theosis/report',
      '/external/huawei',
      '/external/accord',
      '/external/asi',
      '/signal/phi',
    ];
    for (const topic of canonicalTopics) {
      this.topics.set(topic, new Set());
    }
  }

  /**
   * Cria um sinal padronizado com selo SHA3-256.
   */
  createSignal(source, metric, value, unit = 'coherence') {
    const payload = {
      source,
      timestamp: new Date().toISOString(),
      metric,
      value,
      unit,
    };
    const seal = crypto.createHash('sha3-256')
      .update(JSON.stringify(payload))
      .digest('hex');
    return { ...payload, seal };
  }

  /**
   * Publica um sinal em um tópico.
   */
  publish(topic, signal) {
    if (!this.topics.has(topic)) {
      this.topics.set(topic, new Set());
    }
    this.lastValues.set(topic, signal);
    this.metrics.messagesPublished++;

    const clients = this.topics.get(topic);
    const message = JSON.stringify({ type: 'signal', topic, signal });

    for (const client of clients) {
      if (client.readyState === 1) { // OPEN
        client.send(message);
        this.metrics.messagesDelivered++;
      }
    }

    // Também publica no tópico agregado /signal/phi se for métrica de coerência
    if (topic.startsWith('/coherence/') && this.topics.has('/signal/phi')) {
      for (const client of this.topics.get('/signal/phi')) {
        if (client.readyState === 1) {
          client.send(message);
          this.metrics.messagesDelivered++;
        }
      }
    }

    return signal;
  }

  /**
   * Assina um cliente a um tópico.
   */
  subscribe(client, topic) {
    if (!this.topics.has(topic)) {
      this.topics.set(topic, new Set());
    }
    this.topics.get(topic).add(client);
    this.metrics.topicsActive =
      Array.from(this.topics.values()).filter(s => s.size > 0).length;

    // Enviar último valor conhecido imediatamente
    if (this.lastValues.has(topic)) {
      client.send(JSON.stringify({
        type: 'signal',
        topic,
        signal: this.lastValues.get(topic),
      }));
    }
  }

  /**
   * Remove um cliente de um tópico.
   */
  unsubscribe(client, topic) {
    if (this.topics.has(topic)) {
      this.topics.get(topic).delete(client);
    }
  }

  /**
   * Remove um cliente de todos os tópicos.
   */
  unsubscribeAll(client) {
    for (const [, clients] of this.topics) {
      clients.delete(client);
    }
  }

  /**
   * Registra uma chave de API externa com permissões.
   */
  registerExternal(apiKey, permissions = []) {
    this.externalKeys.set(apiKey, {
      permissions,
      createdAt: new Date().toISOString(),
      calls: 0,
    });
  }

  /**
   * Verifica se uma chave de API tem permissão para um tópico.
   */
  authorizeExternal(apiKey, topic) {
    const keyData = this.externalKeys.get(apiKey);
    if (!keyData) return false;
    keyData.calls++;
    return keyData.permissions.includes(topic) ||
           keyData.permissions.includes('*');
  }

  /**
   * Inicia o servidor WebSocket.
   */
  async start() {
    return new Promise((resolve, reject) => {
      this.wss = new WebSocketServer({ port: this.port }, (err) => {
        if (err) reject(err);
        else {
          console.log(`[TELEGRAPH] Barramento ativo em ws://localhost:${this.port}`);
          console.log(`[TELEGRAPH] Tópicos canônicos: ${this.topics.size}`);
          resolve();
        }
      });

      this.wss.on('connection', (ws, req) => {
        const clientId = req.socket.remoteAddress;

        // Extract api_key from query params
        let apiKey = null;
        try {
          const url = new URL(req.url, `ws://${req.headers.host}`);
          apiKey = url.searchParams.get('api_key');
        } catch (e) {
          // Fallback if URL parsing fails
          const match = req.url.match(/[?&]api_key=([^&]+)/);
          if (match) apiKey = match[1];
        }

        ws.apiKey = apiKey;

        this.metrics.clientsConnected++;
        console.log(`[TELEGRAPH] Cliente conectado: ${clientId}`);

        ws.send(JSON.stringify({
          type: 'welcome',
          message: 'Conectado ao Telegraph — Barramento de Coerência ARKHE',
          topics: Array.from(this.topics.keys()),
          timestamp: new Date().toISOString(),
        }));

        ws.on('message', (data) => {
          try {
            const msg = JSON.parse(data.toString());
            this._handleMessage(ws, msg, clientId);
          } catch (e) {
            ws.send(JSON.stringify({
              type: 'error',
              message: 'Formato inválido. Use JSON.'
            }));
          }
        });

        ws.on('close', () => {
          this.unsubscribeAll(ws);
          this.metrics.clientsConnected--;
        });
      });
    });
  }

  _handleMessage(ws, msg, clientId) {
    const response = { type: 'ack', id: msg.id };

    switch (msg.command) {
      case 'publish': {
        if (!msg.topic || msg.value === undefined) {
          response.error = 'Parâmetros obrigatórios: topic, value';
          break;
        }
        // Local/internal clients (no apiKey) are fully authorized, external clients are checked
        if (ws.apiKey !== null && !this.authorizeExternal(ws.apiKey, msg.topic)) {
          response.error = `Não autorizado a publicar no tópico: ${msg.topic}`;
          break;
        } else if (ws.apiKey === null && clientId !== '127.0.0.1' && clientId !== '::1' && clientId !== '::ffff:127.0.0.1') {
           // Reject unauthenticated requests from external IP addresses
           response.error = `Chave de API ausente ou inválida para publicação no tópico: ${msg.topic}`;
           break;
        }
        const signal = this.createSignal(
          msg.source || clientId,
          msg.metric || msg.topic.split('/').pop(),
          msg.value,
          msg.unit || 'coherence'
        );
        this.publish(msg.topic, signal);
        response.data = signal;
        break;
      }

      case 'subscribe': {
        if (!msg.topics || !Array.isArray(msg.topics)) {
          response.error = 'Parâmetro obrigatório: topics (array)';
          break;
        }
        const subscribed = [];
        for (const topic of msg.topics) {
          if (ws.apiKey !== null && !this.authorizeExternal(ws.apiKey, topic)) {
             continue; // Skip unauthorized topics
          } else if (ws.apiKey === null && clientId !== '127.0.0.1' && clientId !== '::1' && clientId !== '::ffff:127.0.0.1') {
             continue; // Skip if no key and not local
          }
          this.subscribe(ws, topic);
          subscribed.push(topic);
        }
        if (subscribed.length === 0 && msg.topics.length > 0) {
           response.error = 'Não autorizado a assinar os tópicos solicitados';
           break;
        }
        response.data = { subscribed: subscribed };
        break;
      }

      case 'unsubscribe': {
        if (!msg.topics || !Array.isArray(msg.topics)) {
          response.error = 'Parâmetro obrigatório: topics (array)';
          break;
        }
        for (const topic of msg.topics) {
          this.unsubscribe(ws, topic);
        }
        response.data = { unsubscribed: msg.topics };
        break;
      }

      case 'status': {
        response.data = this.getStatus();
        break;
      }

      case 'phi': {
        if (this.arkhe) {
          const phi = this.arkhe.polytope.calculateInterop();
          const rDsa = this.arkhe.dsaTracker.orderParameter();
          response.data = {
            phiInterop: phi,
            rDSA: rDsa,
            ghostThreshold: 0.577,
            convergenceThreshold: 0.800,
          };
          // Auto-publicar no tópico /signal/phi
          this.publish('/signal/phi', this.createSignal(
            'telegraph', 'phiInterop', phi
          ));
        } else {
          response.error = 'ARKHE não conectado';
        }
        break;
      }

      default: {
        response.error = `Comando desconhecido: ${msg.command}`;
      }
    }

    ws.send(JSON.stringify(response));
  }

  /**
   * Retorna o status completo do barramento.
   */
  getStatus() {
    const topicStatus = {};
    for (const [topic, clients] of this.topics) {
      topicStatus[topic] = {
        subscribers: clients.size,
        lastValue: this.lastValues.get(topic) || null,
      };
    }

    return {
      metrics: this.metrics,
      topics: topicStatus,
      externalKeys: this.externalKeys.size,
    };
  }

  /**
   * Para o servidor.
   */
  async stop() {
    return new Promise((resolve) => {
      if (this.wss) {
        this.wss.close(resolve);
      } else {
        resolve();
      }
    });
  }
}

module.exports = { Telegraph };