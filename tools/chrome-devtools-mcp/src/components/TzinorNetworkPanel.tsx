
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Network, ArrowRightLeft, Zap, Clock, Database } from 'lucide-react';
import React from 'react';

export interface TzinorEnvelope {
  id: string;
  sender: string;
  recipient: string;
  type: 'PHASE' | 'COHERENCE' | 'TEMPORAL' | 'GEOMETRY' | 'CONSCIOUSNESS';
  lambda: number;
  timestamp?: string;
}

export interface TzinorNetworkState {
  activeChannels: number;
  envelopesTransmitted: number;
  envelopesReceived: number;
  recentTraffic: TzinorEnvelope[];
  primaryAnchor: string;
}

export default function TzinorNetworkPanel({ network }: { network: TzinorNetworkState }) {
  const getTypeColor = (type: string) => {
    switch (type) {
      case 'PHASE': return 'text-arkhe-cyan border-arkhe-cyan/30 bg-arkhe-cyan/10';
      case 'COHERENCE': return 'text-arkhe-green border-arkhe-green/30 bg-arkhe-green/10';
      case 'TEMPORAL': return 'text-arkhe-orange border-arkhe-orange/30 bg-arkhe-orange/10';
      case 'GEOMETRY': return 'text-purple-400 border-purple-400/30 bg-purple-400/10';
      case 'CONSCIOUSNESS': return 'text-pink-400 border-pink-400/30 bg-pink-400/10';
      default: return 'text-arkhe-muted border-arkhe-border bg-[#1f2024]';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'PHASE': return <Zap className="w-3 h-3" />;
      case 'COHERENCE': return <Network className="w-3 h-3" />;
      case 'TEMPORAL': return <Clock className="w-3 h-3" />;
      case 'GEOMETRY': return <Database className="w-3 h-3" />;
      default: return <ArrowRightLeft className="w-3 h-3" />;
    }
  };

  return (
    <div className="bg-[#111214] border border-arkhe-border rounded-xl p-4 flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <ArrowRightLeft className="w-5 h-5 text-arkhe-cyan" />
          <h2 className="text-sm font-bold uppercase tracking-widest text-arkhe-cyan">Tzinor gRPC Streams</h2>
        </div>
        <div className="text-xs font-mono text-arkhe-muted bg-[#1f2024] px-2 py-1 rounded border border-arkhe-border">
          ANCHOR: <span className="text-arkhe-orange">{network.primaryAnchor}</span>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="bg-black/40 p-3 rounded-lg border border-arkhe-border/50">
          <div className="text-[10px] font-mono text-arkhe-muted mb-1 uppercase">Active Channels</div>
          <div className="text-lg font-mono text-arkhe-cyan">{network.activeChannels}</div>
        </div>
        <div className="bg-black/40 p-3 rounded-lg border border-arkhe-border/50">
          <div className="text-[10px] font-mono text-arkhe-muted mb-1 uppercase">TX Envelopes</div>
          <div className="text-lg font-mono text-arkhe-text">{network.envelopesTransmitted.toLocaleString()}</div>
        </div>
        <div className="bg-black/40 p-3 rounded-lg border border-arkhe-border/50">
          <div className="text-[10px] font-mono text-arkhe-muted mb-1 uppercase">RX Envelopes</div>
          <div className="text-lg font-mono text-arkhe-text">{network.envelopesReceived.toLocaleString()}</div>
        </div>
      </div>

      <div className="bg-[#1f2024]/50 p-3 rounded-lg border border-arkhe-green/30 mb-4">
        <div className="flex items-center justify-between mb-2">
          <div className="text-[10px] font-mono text-arkhe-green uppercase flex items-center gap-1">
            <Database className="w-3 h-3" /> Genesis Anchor Verified
          </div>
          <a href="https://etherscan.io/verifySig/303724" target="_blank" rel="noreferrer" className="text-[10px] font-mono text-arkhe-cyan hover:underline">
            View on Etherscan ↗
          </a>
        </div>
        <div className="text-[10px] font-mono text-arkhe-muted break-all">
          <span className="text-arkhe-text">Signer:</span> 0xbf7da1f568684889a69a5bed9f1311f703985590
        </div>
        <div className="text-[10px] font-mono text-arkhe-muted break-all mt-1">
          <span className="text-arkhe-text">Hash:</span> 0x504ce19414dca67777f8db2390fd3d896c9a8e7d94d87368484e1cb125fb000b787c1cea0cb57ec5658812f2317f6b37e104c55110fc0ad98acc1f30227506051b
        </div>
      </div>

      <div className="bg-[#1f2024]/50 p-3 rounded-lg border border-arkhe-cyan/30 mb-4">
        <div className="flex items-center justify-between mb-2">
          <div className="text-[10px] font-mono text-arkhe-cyan uppercase flex items-center gap-1">
            <ArrowRightLeft className="w-3 h-3" /> Tzinor Channel Verified
          </div>
          <a href="https://etherscan.io/verifySig/303856" target="_blank" rel="noreferrer" className="text-[10px] font-mono text-arkhe-cyan hover:underline">
            View on Etherscan ↗
          </a>
        </div>
        <div className="text-[10px] font-mono text-arkhe-muted break-all">
          <span className="text-arkhe-text">Message:</span> Tzinor Channel (2008 ↔ 2140): 1929027937031389406348443648.000000
        </div>
        <div className="text-[10px] font-mono text-arkhe-muted break-all mt-1">
          <span className="text-arkhe-text">Hash:</span> 0xe30eba53c5ee3ef00e76628416d4080c3316e59ede7c7ec748115f332fa66d087231b3cb7ef238b917273cdb4e7c97531b1d0ba7b30cc12da3c01f5b30af6f8e1b
        </div>
      </div>

      <div className="flex-1 flex flex-col min-h-[200px]">
        <h3 className="text-[10px] font-mono text-arkhe-muted uppercase mb-2">Live Envelope Traffic</h3>
        <div className="flex-1 bg-black/60 rounded-lg border border-arkhe-border/50 overflow-hidden flex flex-col">
          <div className="grid grid-cols-12 gap-2 p-2 border-b border-arkhe-border/50 bg-[#1f2024]/50 text-[10px] font-mono text-arkhe-muted uppercase">
            <div className="col-span-2">Time</div>
            <div className="col-span-3">Source</div>
            <div className="col-span-3">Target</div>
            <div className="col-span-2">Payload</div>
            <div className="col-span-2 text-right">λ₂</div>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {network.recentTraffic.map((env) => (
              <div key={env.id} className="grid grid-cols-12 gap-2 items-center text-[10px] font-mono p-1.5 rounded hover:bg-[#1f2024] transition-colors border border-transparent hover:border-arkhe-border/50">
                <div className="col-span-2 text-arkhe-muted">{env.timestamp || '00:00:00'}</div>
                <div className="col-span-3 text-arkhe-text truncate" title={env.sender}>{env.sender}</div>
                <div className="col-span-3 text-arkhe-text truncate" title={env.recipient}>{env.recipient}</div>
                <div className="col-span-2">
                  <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded border ${getTypeColor(env.type)}`}>
                    {getTypeIcon(env.type)}
                    <span className="text-[9px]">{env.type}</span>
                  </span>
                </div>
                <div className={`col-span-2 text-right ${env.lambda >= 1.618 ? 'text-arkhe-green' : 'text-arkhe-orange'}`}>
                  {env.lambda.toFixed(3)}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
