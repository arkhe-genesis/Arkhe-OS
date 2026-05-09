
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Network, Server, Activity } from 'lucide-react';
import React from 'react';

interface EdgeState {
  activePhysicalNodes: number;
  mcpConnections: string[];
  phase: number;
}

export default function EdgeAgentPanel({ edge }: { edge: EdgeState }) {
  return (
    <div className="bg-[#111214] border border-arkhe-border rounded-xl p-4 flex flex-col h-full">
      <div className="flex items-center gap-2 mb-4">
        <Network className="w-5 h-5 text-arkhe-cyan" />
        <h2 className="text-sm font-bold uppercase tracking-widest text-arkhe-cyan">Omnipresent Edge Layer</h2>
      </div>

      <div className="space-y-4 flex-1">
        <div className="bg-black/40 p-3 rounded-lg border border-arkhe-border/50">
          <div className="text-xs font-mono text-arkhe-muted mb-1 uppercase">Active Physical Nodes</div>
          <div className="text-xl font-mono text-arkhe-text flex items-center gap-2">
            <Activity className="w-4 h-4 text-arkhe-green animate-pulse" />
            {edge.activePhysicalNodes.toLocaleString()}
          </div>
        </div>

        <div className="bg-black/40 p-3 rounded-lg border border-arkhe-border/50">
          <div className="text-xs font-mono text-arkhe-muted mb-1 uppercase">Phase Synchronization</div>
          <div className="text-xl font-mono text-arkhe-text">
            λ {edge.phase.toFixed(4)}
          </div>
        </div>

        <div className="bg-black/40 p-3 rounded-lg border border-arkhe-border/50 flex-1">
          <div className="text-xs font-mono text-arkhe-muted mb-2 uppercase">MCP Connections</div>
          <div className="space-y-2">
            {edge.mcpConnections.map((conn, i) => (
              <div key={i} className="flex items-center gap-2 text-xs font-mono bg-arkhe-cyan/5 text-arkhe-cyan p-2 rounded border border-arkhe-cyan/20">
                <Server className="w-3 h-3" />
                <span className="truncate">{conn}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
