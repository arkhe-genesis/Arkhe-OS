
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */


import { Network, Server, ShieldCheck, Zap, Repeat } from 'lucide-react';

import type { Shard } from '../../server/types';

import { Card } from './ui/Card';

interface NetworkStatusProps {
  shards: Shard[];
}

export default function NetworkStatus({ shards }: NetworkStatusProps) {
  const totalShards = 24;
  const dataShards = 16;

  const activeCount = shards.filter(s => s.status === 'active').length;
  const isDegraded = activeCount < totalShards;
  const isCritical = activeCount < dataShards;

  return (
    <Card
      title="Tzinor GNSS Network"
      icon={<Network className="w-4 h-4" />}
      status={isCritical ? 'critical' : isDegraded ? 'warning' : 'normal'}
    >
      <div className="mb-6">
        <div className="text-xs font-mono text-arkhe-muted uppercase mb-2">Reed-Solomon Shards [16,24]</div>
        <div className="grid grid-cols-8 gap-1">
          {shards.map((shard, i) => {
            const isData = i < dataShards;

            let bgColor = 'bg-[#1f2024]';
            if (shard.status === 'active') {
              bgColor = isData ? 'bg-arkhe-cyan' : 'bg-arkhe-green';
            } else if (shard.status === 'corrupted') {
              bgColor = 'bg-arkhe-red animate-pulse';
            } else if (shard.status === 'recovering') {
              bgColor = 'bg-arkhe-orange animate-pulse';
            }

            return (
              <div
                key={shard.id}
                className={`h-6 rounded-sm ${bgColor} border border-black/20 transition-colors duration-300`}
                title={isData ? `Data Shard ${i+1} - ${shard.status}` : `Parity Shard ${i-dataShards+1} - ${shard.status}`}
              />
            );
          })}
        </div>
        <div className="flex justify-between mt-2 text-[10px] font-mono text-arkhe-muted uppercase">
          <span>Data (16)</span>
          <span>Parity (8)</span>
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex justify-between items-center p-2 bg-[#151619] rounded border border-arkhe-border">
          <div className="flex items-center gap-2">
            <Server className="w-3 h-3 text-arkhe-muted" />
            <span className="text-xs font-mono text-arkhe-muted uppercase">PNT Consensus</span>
          </div>
          <span className={`text-xs font-mono font-bold ${isCritical ? 'text-arkhe-red' : 'text-arkhe-green'}`}>
            {isCritical ? 'FAILED' : 'REACHED'}
          </span>
        </div>

        <div className="flex justify-between items-center p-2 bg-[#151619] rounded border border-arkhe-border">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full border-2 border-arkhe-muted flex items-center justify-center">
              <div className="w-1 h-1 bg-arkhe-muted rounded-full" />
            </div>
            <span className="text-xs font-mono text-arkhe-muted uppercase">Timechain Anchor</span>
          </div>
          <span className="text-xs font-mono font-bold text-arkhe-cyan">SYNCED</span>
        </div>

        <div className="flex justify-between items-center p-2 bg-[#1a1b1e] rounded border border-arkhe-border/50 group hover:border-arkhe-cyan/30 transition-colors">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-3 h-3 text-arkhe-cyan group-hover:animate-pulse" />
            <span className="text-[10px] font-mono text-arkhe-muted uppercase">Recursive ZK-Health (1000 nodes)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono font-bold text-arkhe-green">VERIFIED</span>
            <div className="w-1.5 h-1.5 rounded-full bg-arkhe-green animate-pulse" />
          </div>
        </div>

        <div className="flex justify-between items-center p-2 bg-[#1a1b1e] rounded border border-arkhe-border/50 group hover:border-arkhe-orange/30 transition-colors">
          <div className="flex items-center gap-2">
            <Zap className="w-3 h-3 text-arkhe-orange" />
            <span className="text-[10px] font-mono text-arkhe-muted uppercase">Selection Beacon (QRB+VDF)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono font-bold text-arkhe-orange">ACTIVE</span>
            <div className="w-1.5 h-1.5 rounded-full bg-arkhe-orange animate-ping" />
          </div>
        </div>

        <div className="flex justify-between items-center p-2 bg-[#1a1b1e] rounded border border-arkhe-border/50 group hover:border-arkhe-purple/30 transition-colors">
          <div className="flex items-center gap-2">
            <Repeat className="w-3 h-3 text-arkhe-purple animate-spin-slow" />
            <span className="text-[10px] font-mono text-arkhe-muted uppercase">Quantum Handover (Teleport)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono font-bold text-arkhe-purple">READY</span>
            <div className="w-1.5 h-1.5 rounded-full bg-arkhe-purple" />
          </div>
        </div>
      </div>
    </Card>
  );
}
