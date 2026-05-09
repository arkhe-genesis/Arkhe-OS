
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */


import { Link } from 'lucide-react';

import type { OrbLog } from '../../server/types';

import { Card } from './ui/Card';

interface TimechainVisualizerProps {
  logs: OrbLog[];
}

export default function TimechainVisualizer({ logs }: TimechainVisualizerProps) {
  // Take the most recent 10 logs to visualize as blocks
  const blocks = logs.slice(0, 10).reverse();

  return (
    <Card
      title="Timechain Topology"
      icon={<Link className="w-4 h-4" />}
    >
      <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-arkhe-border scrollbar-track-transparent">
        {blocks.map((block, i) => {
          const isRejected = block.status === 'Rejected';
          const isMitigated = block.status === 'Mitigated';
          const isLatest = i === blocks.length - 1;

          return (
            <div key={block.id} className="flex items-center shrink-0">
              {/* Block */}
              <div
                className={`w-24 p-2 rounded border flex flex-col gap-1 relative ${
                  isRejected ? 'bg-arkhe-red/10 border-arkhe-red/50' :
                  isMitigated ? 'bg-arkhe-orange/10 border-arkhe-orange/50' :
                  'bg-[#151619] border-arkhe-border'
                } ${isLatest ? 'ring-1 ring-arkhe-cyan shadow-[0_0_10px_rgba(0,229,255,0.2)]' : ''}`}
              >
                <div className="text-[8px] font-mono text-arkhe-muted uppercase truncate">
                  ID: {block.id.substring(0, 6)}
                </div>
                <div className={`text-[10px] font-mono font-bold ${
                  isRejected ? 'text-arkhe-red' :
                  isMitigated ? 'text-arkhe-orange' :
                  'text-arkhe-cyan'
                }`}>
                  λ₂: {block.coherence.toFixed(3)}
                </div>
                <div className="text-[8px] font-mono text-arkhe-muted truncate">
                  {new Date(block.targetTime || 0).toLocaleTimeString('en-US', { hour12: false, second: '2-digit', minute: '2-digit' })}
                </div>
                {block.threatType && (
                  <div className="absolute -top-2 -right-2 bg-arkhe-red text-black text-[8px] font-bold px-1 rounded animate-pulse">
                    !
                  </div>
                )}
              </div>

              {/* Link to next block */}
              {i < blocks.length - 1 && (
                <div className="w-6 h-[2px] bg-arkhe-border relative">
                  <div className="absolute right-0 top-1/2 -translate-y-1/2 w-1.5 h-1.5 border-t-2 border-r-2 border-arkhe-border rotate-45" />
                </div>
              )}
            </div>
          );
        })}
        {blocks.length === 0 && (
          <div className="text-xs font-mono text-arkhe-muted py-4 text-center w-full">
            Initializing Timechain Genesis Block...
          </div>
        )}
      </div>
    </Card>
  );
}
