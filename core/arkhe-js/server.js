#!/usr/bin/env node
/**
 * ═══════════════════════════════════════════════════════════════════
 * ARKHE.WS — Servidor WebSocket para monitoramento do Φ_interop
 * Substrato: 765-ARKHE-OS-GEOMETRIC-REFACTOR (Hook 765.2)
 * Versão: 1.0.0
 * Uso: node server.js [--port=3000]
 * ═══════════════════════════════════════════════════════════════════
 */

'use strict';

const { WebSocketServer } = require('ws');
const { Arkhe, CONSTANTS } = require('./arkhe.js');

// Configuração
const PORT = process.env.PORT || 3000;
const arkhe = new Arkhe();

// Estados de assinatura dos clientes
const subscribers = new Map(); // ws -> intervalID

// Iniciar servidor HTTP + WebSocket
const wss = new WebSocketServer({ port: PORT });

console.log(`[ARKHE.WS] Servidor WebSocket iniciado na porta ${PORT}`);
console.log(`[ARKHE.WS] Φ_interop inicial = ${arkhe.polytope.calculateInterop().toFixed(6)}`);

wss.on('connection', (ws, req) => {
  const clientIP = req.socket.remoteAddress;
  console.log(`[ARKHE.WS] Cliente conectado: ${clientIP}`);

  // Enviar status inicial
  ws.send(JSON.stringify({
    type: 'welcome',
    version: arkhe.version,
    phiInterop: arkhe.polytope.calculateInterop(),
    timestamp: Date.now()
  }));

  ws.on('message', (data) => {
    let msg;
    try {
      msg = JSON.parse(data.toString());
    } catch (e) {
      ws.send(JSON.stringify({ error: 'Formato inválido. Use JSON.' }));
      return;
    }

    const response = { id: msg?.id, timestamp: Date.now() };

    try {
      switch (msg.command) {
        case 'status':
          response.data = arkhe.status();
          break;

        case 'solve':
          if (!msg.pattern || typeof msg.problem !== 'number') {
            response.error = 'Parâmetros obrigatórios: pattern, problem';
          } else {
            response.data = arkhe.dsaTracker.solve(msg.pattern, msg.problem);
          }
          break;

        case 'init-kuramoto':
          {
            const N = Math.min(10000, Math.max(1, msg.N || 512));
            const K = msg.K || CONSTANTS.K_BASE_DEFAULT;
            arkhe.initKuramoto(N, K);
            response.data = {
              success: true,
              N,
              K,
              r: arkhe.kuramoto.orderParameter()
            };
          }
          break;

        case 'simulate':
          if (!arkhe.kuramoto) {
            response.error = 'Kuramoto não inicializado. Use init-kuramoto primeiro.';
          } else {
            const T = msg.T || 50;
            const dt = msg.dt || 0.02;
            const history = arkhe.kuramoto.simulate(T, dt);
            response.data = {
              history,
              finalR: history[history.length - 1]?.r || 0
            };
          }
          break;

        case 'subscribe':
          // Ativar envio periódico de Φ_interop
          if (subscribers.has(ws)) {
            clearInterval(subscribers.get(ws));
          }
          const interval = setInterval(() => {
            if (ws.readyState === ws.OPEN) {
              ws.send(JSON.stringify({
                type: 'phi_update',
                phiInterop: arkhe.polytope.calculateInterop(),
                timestamp: Date.now()
              }));
            } else {
              clearInterval(interval);
              subscribers.delete(ws);
            }
          }, msg.interval || 1000);
          subscribers.set(ws, interval);
          response.data = { subscribed: true, interval: msg.interval || 1000 };
          break;

        case 'unsubscribe':
          if (subscribers.has(ws)) {
            clearInterval(subscribers.get(ws));
            subscribers.delete(ws);
          }
          response.data = { subscribed: false };
          break;

        case 'phi':
          response.data = {
            phiInterop: arkhe.polytope.calculateInterop(),
            phiC: arkhe.polytope.phiC,
            rDSA: arkhe.dsaTracker.orderParameter(),
            ghostThreshold: CONSTANTS.GHOST_THRESHOLD,
            convergenceThreshold: CONSTANTS.CONVERGENCE_THRESHOLD
          };
          break;

        default:
          response.error = `Comando desconhecido: ${msg.command}`;
      }
    } catch (e) {
      response.error = e.message;
    }

    ws.send(JSON.stringify(response));
  });

  ws.on('close', () => {
    if (subscribers.has(ws)) {
      clearInterval(subscribers.get(ws));
      subscribers.delete(ws);
    }
    console.log(`[ARKHE.WS] Cliente desconectado: ${clientIP}`);
  });
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n[ARKHE.WS] Encerrando servidor...');
  for (const [ws, interval] of subscribers) {
    clearInterval(interval);
    ws.terminate();
  }
  wss.close();
  process.exit(0);
});

console.log('[ARKHE.WS] Comandos disponíveis: status, solve, init-kuramoto, simulate, subscribe, unsubscribe, phi');
console.log('[ARKHE.WS] Exemplo: ws.send(JSON.stringify({command:"status"}))');
