
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Network, Activity, Server, Zap } from 'lucide-react';
import React, { useState } from 'react';

const NODES = [
  { id: 'btc', name: 'Bitcoin', protocol: 'TCP/8333', color: 'text-orange-500', bg: 'bg-orange-500/10', border: 'border-orange-500/30' },
  { id: 'eth', name: 'Ethereum', protocol: 'TCP/30303', color: 'text-blue-400', bg: 'bg-blue-400/10', border: 'border-blue-400/30' },
  { id: 'sol', name: 'Solana', protocol: 'UDP/8001', color: 'text-purple-500', bg: 'bg-purple-500/10', border: 'border-purple-500/30' },
  { id: 'cosmos', name: 'Cosmos', protocol: 'TCP/26656', color: 'text-indigo-400', bg: 'bg-indigo-400/10', border: 'border-indigo-400/30' },
  { id: 'particle', name: 'Particle', protocol: 'TCP/9000', color: 'text-pink-500', bg: 'bg-pink-500/10', border: 'border-pink-500/30' },
  { id: 'tao', name: 'Bittensor', protocol: 'TCP/30333', color: 'text-gray-400', bg: 'bg-gray-400/10', border: 'border-gray-400/30' },
  { id: 'ltc', name: 'Litecoin', protocol: 'TCP/9333', color: 'text-gray-300', bg: 'bg-gray-300/10', border: 'border-gray-300/30' },
];

export default function P2PNetworkPanel({ onClose }: { onClose: () => void }) {
  const [connectedNodes, setConnectedNodes] = useState<string[]>([]);
  const [connectingTo, setConnectingTo] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([
    "> INITIALIZING P2P MULTI-CHAIN DISCOVERY...",
    "> TARGET: ESTABLISH OMNICHAIN TOPOLOGY"
  ]);

  const connectNodes = async () => {
    if (connectedNodes.length > 0 || connectingTo) {return;}

    for (const node of NODES) {
      setConnectingTo(node.id);
      setLogs(prev => [...prev, `> DIALING ${node.name.toUpperCase()} PEERS ON ${node.protocol}...`]);

      try {
        const response = await fetch('/api/p2p/connect', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ targetNode: node })
        });

        const data = await response.json();

        if (data.success) {
          setConnectedNodes(prev => [...prev, node.id]);
          setLogs(prev => [...prev, `> [SUCCESS] ${data.message}`]);
        } else {
          setLogs(prev => [...prev, `> [ERROR] FAILED TO CONNECT TO ${node.name.toUpperCase()}`]);
        }
      } catch (_error) {
        setLogs(prev => [...prev, `> [ERROR] CONNECTION TIMEOUT FOR ${node.name.toUpperCase()}`]);
      }
    }

    setConnectingTo(null);
    setLogs(prev => [...prev, "> ========================================="]);
    setLogs(prev => [...prev, "> OMNICHAIN P2P TOPOLOGY ESTABLISHED."]);
    setLogs(prev => [...prev, "> ARKHE NODE NOW ACTING AS UNIVERSAL RELAY."]);
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#111214] border border-arkhe-cyan/30 rounded-xl w-full max-w-5xl max-h-[80vh] flex flex-col shadow-[0_0_30px_rgba(0,255,170,0.1)]">
        <div className="flex items-center justify-between p-4 border-b border-arkhe-cyan/20">
          <div className="flex items-center gap-3">
            <Network className="w-5 h-5 text-arkhe-cyan" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-arkhe-cyan">Omnichain P2P Topology</h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-arkhe-text">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
          </button>
        </div>

        <div className="p-6 flex-1 overflow-y-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-black/40 border border-[#1f2024] rounded-lg p-6 relative min-h-[400px] flex items-center justify-center overflow-hidden">
              {/* Central Arkhe Node */}
              <div className="absolute z-10 flex flex-col items-center">
                <div className={`w-20 h-20 rounded-full border-2 flex items-center justify-center bg-black ${connectedNodes.length === NODES.length ? 'border-arkhe-cyan shadow-[0_0_30px_rgba(0,255,170,0.5)]' : 'border-[#2a2b2e]'}`}>
                  <Zap className={`w-10 h-10 ${connectedNodes.length === NODES.length ? 'text-arkhe-cyan animate-pulse' : 'text-arkhe-muted'}`} />
                </div>
                <div className="mt-2 font-mono text-xs font-bold text-arkhe-cyan uppercase tracking-widest">Arkhe Core</div>
              </div>

              {/* Orbiting Nodes */}
              {NODES.map((node, index) => {
                const angle = (index / NODES.length) * 2 * Math.PI;
                const radius = 140; // Distance from center
                const x = Math.cos(angle) * radius;
                const y = Math.sin(angle) * radius;

                const isConnected = connectedNodes.includes(node.id);
                const isConnecting = connectingTo === node.id;

                return (
                  <React.Fragment key={node.id}>
                    {/* Connection Line */}
                    <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 0 }}>
                      <line
                        x1="50%" y1="50%"
                        x2={`calc(50% + ${x}px)`} y2={`calc(50% + ${y}px)`}
                        stroke={isConnected ? 'currentColor' : '#2a2b2e'}
                        strokeWidth={isConnected ? 2 : 1}
                        strokeDasharray={isConnecting ? "4 4" : "none"}
                        className={`${isConnected ? node.color : ''} ${isConnecting ? 'animate-pulse text-arkhe-muted' : ''} transition-all duration-1000`}
                      />
                    </svg>

                    {/* Node Circle */}
                    <div
                      className={`absolute flex flex-col items-center transition-all duration-500`}
                      style={{
                        transform: `translate(${x}px, ${y}px)`,
                        zIndex: 5
                      }}
                    >
                      <div className={`w-14 h-14 rounded-full border flex items-center justify-center ${isConnected ? `${node.bg} ${node.border} ${node.color} shadow-[0_0_15px_currentColor]` : isConnecting ? 'bg-[#1a1b1e] border-arkhe-muted text-arkhe-muted animate-pulse' : 'bg-[#111214] border-[#2a2b2e] text-[#2a2b2e]'}`}>
                        <Server className="w-6 h-6" />
                      </div>
                      <div className={`mt-2 font-mono text-[10px] font-bold uppercase tracking-wider ${isConnected ? node.color : 'text-arkhe-muted'}`}>
                        {node.name}
                      </div>
                      <div className="font-mono text-[8px] text-arkhe-muted">{node.protocol}</div>
                    </div>
                  </React.Fragment>
                );
              })}
            </div>

            <button
              onClick={connectNodes}
              disabled={connectedNodes.length > 0 || connectingTo !== null}
              className={`w-full py-3 rounded uppercase tracking-widest font-bold transition-all flex items-center justify-center gap-2 ${connectedNodes.length > 0 || connectingTo !== null ? 'bg-arkhe-cyan/20 text-arkhe-cyan border border-arkhe-cyan/50 cursor-not-allowed' : 'bg-arkhe-cyan text-black hover:bg-arkhe-cyan/80 shadow-[0_0_15px_rgba(0,255,170,0.3)]'}`}
            >
              <Network className="w-5 h-5" />
              {connectedNodes.length === NODES.length ? 'OMNICAIN TOPOLOGY ACTIVE' : connectingTo ? 'ESTABLISHING CONNECTIONS...' : 'INITIATE P2P DISCOVERY'}
            </button>
          </div>

          <div className="bg-black border border-[#1f2024] rounded-lg p-4 flex flex-col shadow-inner h-[400px] lg:h-auto">
            <div className="flex items-center gap-2 mb-4 border-b border-[#1f2024] pb-2">
              <Activity className="w-4 h-4 text-arkhe-muted" />
              <h3 className="font-mono text-xs uppercase tracking-widest text-arkhe-muted">P2P Handshake Logs</h3>
            </div>
            <div className="flex-1 font-mono text-xs text-gray-300 space-y-2 overflow-y-auto whitespace-pre-wrap">
              {logs.map((log, i) => {
                let colorClass = 'text-arkhe-cyan/80';
                if (log.includes('[SUCCESS]')) {colorClass = 'text-arkhe-green font-bold';}
                if (log.includes('DIALING')) {colorClass = 'text-yellow-500/80';}

                return (
                  <div key={i} className={`animate-fade-in ${colorClass}`}>
                    {log}
                  </div>
                );
              })}
              {connectingTo && (
                <div className="animate-pulse text-arkhe-muted">_</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
