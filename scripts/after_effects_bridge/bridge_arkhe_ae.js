// License: MIT
const WebSocket = await import("ws");
const net = await import("node:net");

/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import net from "node:net";

import WebSocket from "ws";


const wss = new WebSocket.Server({ port: 8080 });
const clients = [];

// Servidor TCP para o After Effects
const tcpServer = net.createServer((socket) => {
    clients.push(socket);
    console.log('AE conectado.');
    socket.on('close', () => {
        const idx = clients.indexOf(socket);
        if (idx > -1) { clients.splice(idx, 1); }
        if (idx > -1) {clients.splice(idx, 1);}
    });
    socket.on('error', (err) => console.error('Erro AE:', err));
});
tcpServer.listen(9999, () => console.log('Ponte TCP para AE na porta 9999'));

wss.on('connection', (ws) => {
    console.log('ArkheCanvas conectado.');
    ws.on('message', (data) => {
        // Reencaminha para todos os clientes AE conectados
        const jsonStr = data.toString();
        clients.forEach(socket => {
            socket.write(jsonStr + '\n'); // delimitador de mensagem
        });
    });
    ws.on('close', () => console.log('ArkheCanvas desconectado.'));
});
