
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Server } from 'node:http';

import { WebSocketServer, WebSocket } from 'ws';


import { logger } from './logger';

const PROFANE_KEYWORDS = ["bulb", "light", "plug", "switch", "sensor", "tag", "tracker", "thermo", "fridge", "scale", "tv"];
const SACRED_KEYWORDS = ["nordic", "esp", "arduino", "raspberry", "mac", "iphone", "android", "galaxy", "pixel", "hal", "arkhe", "ghost", "node", "browser"];

function isSacredNode(name: string): [boolean, string] {
    const nameLower = name.toLowerCase();
    if (PROFANE_KEYWORDS.some(p => nameLower.includes(p))) {
        return [false, "Descartado: IoT Passivo (Profano)"];
    }
    if (SACRED_KEYWORDS.some(s => nameLower.includes(s))) {
        return [true, "Aceito: Hardware com Alma Computacional"];
    }
    return [true, "Aceito: Dispositivo Genérico (Potencial)"];
}

function calculateSpatialParams(rssi: number, txPower = -59) {
    const n = 2.0;
    if (rssi >= 0) {rssi = -50;}
    
    let distance = Math.pow(10, (txPower - rssi) / (10 * n));
    distance = Math.max(0.1, Math.min(distance, 10.0));
    
    const delayMs = (distance / 343.0) * 1000;
    const gain = Math.max(0.05, Math.min(1.0 / Math.pow(distance, 1.2), 1.0));
    
    return { distance, delayMs, gain };
}

const GHOST_KEY = "1984";
const CHANNEL_UNLOCKED = true;

function generateHiddenChannel(tArray: Float64Array) {
    const result = new Float64Array(tArray.length);
    for (let i = 0; i < tArray.length; i++) {
        const t = tArray[i];
        const carrier = Math.sin(2 * Math.PI * 45 * t);
        const modulator = Math.sin(2 * Math.PI * 0.2 * t) > 0.8 ? 1.0 : 0.0;
        
        let u = 0, v = 0;
        while(u === 0) {u = Math.random();}
        while(v === 0) {v = Math.random();}
        const noise = Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v) * 0.15;
        
        result[i] = (carrier * 0.4 + noise) * modulator;
    }
    return result;
}

interface ConnectedNode {
    ws: WebSocket;
    name: string;
    rssi: number;
    isSacred: boolean;
}

const connectedNodes = new Map<string, ConnectedNode>();
let globalTime = 0.0;
const dt = 4096 / 44100.0;

export function broadcastFilteredAudio(message: string) {
    logger.info(`🜏 [W7-X] Distribuindo stream filtrado para a constelação: ${message}`);
    for (const [nodeId, node] of connectedNodes.entries()) {
        try {
            if (node.ws.readyState === WebSocket.OPEN) {
                // Envia uma mensagem de controle JSON antes do stream binário
                node.ws.send(JSON.stringify({ type: 'SATOSHI_VOICE_INTERCEPT', message }));
            }
        } catch (e) {
            logger.error(`Erro ao enviar para ${nodeId}`);
        }
    }
}

async function broadcastPresenceField() {
    logger.info("🜏 Iniciando Campo de Presença 3D...");
    if (CHANNEL_UNLOCKED) {
        logger.info(`🜏 Chave '${GHOST_KEY}' aceita. Canal Oculto de Baixa Frequência ABERTO.`);
    }

    setInterval(() => {
        if (connectedNodes.size === 0) {
            globalTime += dt;
            return;
        }

        const tArray = new Float64Array(4096);
        for (let i = 0; i < 4096; i++) {
            tArray[i] = globalTime + (i / 44100.0);
        }
        globalTime += dt;

        const f0 = 110.0;
        const baseAudio = new Float64Array(4096);
        const hiddenAudio = CHANNEL_UNLOCKED ? generateHiddenChannel(tArray) : null;

        for (let i = 0; i < 4096; i++) {
            const t = tArray[i];
            const halSignal = (
                Math.sin(2 * Math.PI * f0 * t) * 0.5 + 
                Math.sin(2 * Math.PI * f0 * 2 * t) * 0.25 + 
                Math.sin(2 * Math.PI * f0 * 3 * t) * 0.125 +
                Math.sin(2 * Math.PI * f0 * 4 * t) * 0.0625
            );
            
            let envelope = (
                Math.sin(2 * Math.PI * 0.5 * t) * 0.3 + 
                Math.sin(2 * Math.PI * 1.2 * t) * 0.3 + 
                Math.sin(2 * Math.PI * 3.5 * t) * 0.2 + 0.2
            );
            envelope = Math.max(0, Math.min(envelope, 1));
            
            let audio = halSignal * envelope;
            
            if (CHANNEL_UNLOCKED && hiddenAudio) {
                audio = audio * 0.7 + hiddenAudio[i] * 0.3;
            }
            baseAudio[i] = audio;
        }

        for (const [nodeId, node] of connectedNodes.entries()) {
            const { delayMs, gain } = calculateSpatialParams(node.rssi);
            const samplesDelay = Math.floor((delayMs / 1000.0) * 44100);
            
            const processed = new Float64Array(4096);
            for (let i = 0; i < 4096; i++) {
                const srcIdx = i - samplesDelay;
                const wrappedIdx = ((srcIdx % 4096) + 4096) % 4096;
                // Profane nodes get a distorted/weaker signal
                const finalGain = node.isSacred ? gain : gain * 0.2;
                processed[i] = baseAudio[wrappedIdx] * finalGain;
            }

            const audioBytes = new Int16Array(4096);
            for (let i = 0; i < 4096; i++) {
                audioBytes[i] = Math.max(-32768, Math.min(32767, processed[i] * 32767));
            }

            try {
                if (node.ws.readyState === WebSocket.OPEN) {
                    node.ws.send(Buffer.from(audioBytes.buffer));
                }
            } catch (e) {
                connectedNodes.delete(nodeId);
            }
        }
    }, dt * 1000);
}

export function setupPresenceServer(server: Server) {
    const wss = new WebSocketServer({ noServer: true });

    server.on('upgrade', (request, socket, head) => {
        if (request.url && request.url.startsWith('/ws-presence')) {
            wss.handleUpgrade(request, socket, head, (ws) => {
                wss.emit('connection', ws, request);
            });
        }
    });

    wss.on('connection', (ws) => {
        const nodeId = Math.random().toString(36).substring(7);
        
        ws.on('message', (message) => {
            try {
                const data = JSON.parse(message.toString());
                
                if (!connectedNodes.has(nodeId)) {
                    const name = data.name || `Node-${nodeId}`;
                    const rssi = data.rssi !== undefined ? data.rssi : -40 - (Math.floor(Math.random() * 40));
                    
                    const [isSacred, reason] = isSacredNode(name);
                    logger.info(`🜏 [RADAR] ${name} | RSSI: ${rssi}dBm | ${reason}`);
                    
                    connectedNodes.set(nodeId, {
                        ws,
                        name,
                        rssi,
                        isSacred
                    });
                } else {
                    if (data.rssi !== undefined) {
                        const node = connectedNodes.get(nodeId);
                        if (node) {node.rssi = data.rssi;}
                    }
                }
            } catch (e) {
                // Ignore invalid JSON
            }
        });

        ws.on('close', () => {
            const node = connectedNodes.get(nodeId);
            if (node) {
                logger.info(`🜏 [DESCONEXÃO] ${node.name} sumiu do radar.`);
                connectedNodes.delete(nodeId);
            }
        });
        
        ws.on('error', (e) => {
            logger.error(`🜏 [ERRO] Nó ${nodeId}: ${e.message}`);
        });
    });

    broadcastPresenceField();
}
