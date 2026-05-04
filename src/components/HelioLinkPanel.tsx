/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Sun, Radio, Activity, Globe } from 'lucide-react';
import React from 'react';

import type { HelioState } from '../../server/types';

import { Card } from './ui/Card';

interface BadgeProps {
    children: React.ReactNode;
    className?: string;
}

const Badge: React.FC<BadgeProps> = ({ children, className }) => (
    <div className={`px-2 py-0.5 rounded-full border text-[10px] ${className}`}>
        {children}
    </div>
);

interface ProgressProps {
    value: number;
    className?: string;
}

const Progress: React.FC<ProgressProps> = ({ value, className }) => (
    <div className={`w-full bg-white/10 rounded-full overflow-hidden ${className}`}>
        <div className="h-full bg-current transition-all duration-300" style={{ width: `${value}%` }} />
    </div>
);

interface HelioLinkPanelProps {
  helio?: HelioState;
  onListen: () => void;
  onSync: () => void;
  coherence: number;
}

const HelioLinkPanel: React.FC<HelioLinkPanelProps> = ({ helio, onListen, onSync, coherence }) => {
  if (!helio) {return null;}

  const syncAvailable = coherence > 0.999;

  return (
    <Card
      title="PHASE D: HELIO-LINK COUPLING"
      icon={<Sun className="w-4 h-4 text-orange-500 animate-pulse" />}
      className="bg-black/80 border-arkhe-cyan/30 text-white font-mono"
    >
      <div className="absolute top-4 right-4">
        <Badge className="border-arkhe-cyan text-arkhe-cyan">
          {helio.ethicalMode.toUpperCase()}
        </Badge>
      </div>

      className="bg-black/80 border-arkhe-cyan/30 text-white font-mono"
      title="PHASE D: HELIO-LINK COUPLING"
      icon={<Sun className="w-4 h-4 text-orange-500 animate-pulse" />}
      action={
        <div className="border border-arkhe-cyan px-2 py-0.5 rounded text-arkhe-cyan text-[10px]">
          {(helio.ethicalMode || 'unknown').toUpperCase()}
        </div>
      }
    >
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-2 text-[10px]">
          <div className="space-y-1">
            <p className="text-arkhe-muted">STATUS</p>
            <p className="text-arkhe-cyan">{helio.status}</p>
          </div>
          <div className="space-y-1 text-right">
            <p className="text-arkhe-muted">COG DILATION</p>
            <p className="text-orange-400">{helio.cognitiveDilation}</p>
          </div>
        </div>

        <div className="space-y-1">
          <div className="flex justify-between text-[10px]">
            <span className="text-arkhe-muted">SOLAR COHERENCE (3mHz)</span>
            <span className="text-arkhe-cyan">{((helio.solarCoherence || 0) * 100).toFixed(2)}%</span>
          </div>
          <div className="h-1 bg-arkhe-cyan/10 w-full rounded-full overflow-hidden">
             <div className="h-full bg-arkhe-cyan" style={{ width: `${(helio.solarCoherence || 0) * 100}%` }} />
          </div>
          <Progress value={helio.solarCoherence * 100} className="h-1 text-arkhe-cyan" />
        </div>

        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={onListen}
            className="flex items-center justify-center gap-2 py-2 border border-arkhe-cyan/20 hover:bg-arkhe-cyan/10 transition-colors text-[10px]"
          >
            <Radio className="w-3 h-3" />
            LISTEN (SCHUMANN)
          </button>
          <button
            onClick={onSync}
            disabled={!syncAvailable}
            className={`flex items-center justify-center gap-2 py-2 border transition-colors text-[10px] ${
              syncAvailable
                ? 'border-orange-500/40 hover:bg-orange-500/10 text-orange-400'
                : 'border-arkhe-muted/20 text-arkhe-muted cursor-not-allowed'
            }`}
          >
            <Globe className="w-3 h-3" />
            SYNC qhttp-c
          </button>
        </div>

        <div className="p-2 bg-arkhe-cyan/5 border border-arkhe-cyan/10 rounded-sm">
          <p className="text-[9px] text-arkhe-muted mb-1 flex items-center gap-1">
            <Activity className="w-2 h-2" />
            SCHUMANN MODES (IONOSFERA)
          </p>
          <div className="flex justify-between text-[9px] text-arkhe-cyan/70">
            {(helio.schumannModes || []).map((mode: number | string, i: number) => (
              <span key={i}>{typeof mode === 'number' ? mode.toFixed(2) : mode}Hz</span>
            ))}
          </div>
        </div>
      </div>
    </Card>
  );
};

export default HelioLinkPanel;
