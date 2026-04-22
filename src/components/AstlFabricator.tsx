
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Box, Hexagon, Activity, Clock } from 'lucide-react';
import React from 'react';

export interface AstlState {
  activeMesh: string;
  facets: number;
  coherence: number;
  phaseVolume: number;
  temporalAnchors: string[];
  manifestationProgress: number;
}

export default function AstlFabricator({ astl }: { astl: AstlState }) {
  const isManifestable = astl.coherence >= 1.618;

  return (
    <div className="bg-[#111214] border border-arkhe-border rounded-xl p-4 flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Box className="w-5 h-5 text-arkhe-cyan" />
          <h2 className="text-sm font-bold uppercase tracking-widest text-arkhe-cyan">ASTL Matter Compiler</h2>
        </div>
        <div className={`text-xs font-mono px-2 py-1 rounded border ${isManifestable ? 'bg-arkhe-green/10 text-arkhe-green border-arkhe-green/30' : 'bg-arkhe-orange/10 text-arkhe-orange border-arkhe-orange/30'}`}>
          {isManifestable ? 'MANIFESTING ℝ³' : 'PHASE ALIGNING ℂ'}
        </div>
      </div>
      
      <div className="space-y-4 flex-1">
        <div className="bg-black/40 p-3 rounded-lg border border-arkhe-border/50">
          <div className="flex justify-between items-center mb-2">
            <div className="text-xs font-mono text-arkhe-muted uppercase">Active Mesh</div>
            <div className="text-xs font-mono text-arkhe-cyan">{astl.activeMesh}</div>
          </div>
          <div className="flex justify-between items-center">
            <div className="text-xs font-mono text-arkhe-muted uppercase">Facets</div>
            <div className="text-xs font-mono text-arkhe-text">{astl.facets.toLocaleString()}</div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="bg-black/40 p-3 rounded-lg border border-arkhe-border/50">
            <div className="text-[10px] font-mono text-arkhe-muted mb-1 uppercase flex items-center gap-1">
              <Activity className="w-3 h-3" /> Geometric λ₂
            </div>
            <div className={`text-lg font-mono ${isManifestable ? 'text-arkhe-green' : 'text-arkhe-orange'}`}>
              {astl.coherence.toFixed(4)}
            </div>
          </div>
          <div className="bg-black/40 p-3 rounded-lg border border-arkhe-border/50">
            <div className="text-[10px] font-mono text-arkhe-muted mb-1 uppercase flex items-center gap-1">
              <Hexagon className="w-3 h-3" /> Phase Vol (ℂ)
            </div>
            <div className="text-lg font-mono text-arkhe-text">
              {astl.phaseVolume.toFixed(4)}
            </div>
          </div>
        </div>

        <div className="bg-black/40 p-3 rounded-lg border border-arkhe-border/50">
          <div className="text-[10px] font-mono text-arkhe-muted mb-2 uppercase flex items-center gap-1">
            <Clock className="w-3 h-3" /> Temporal Anchors (ℤ)
          </div>
          <div className="flex gap-2">
            {astl.temporalAnchors.map((anchor, i) => (
              <span key={i} className="text-xs font-mono bg-arkhe-cyan/10 text-arkhe-cyan px-2 py-1 rounded border border-arkhe-cyan/20">
                {anchor}
              </span>
            ))}
          </div>
        </div>

        <div className="mt-auto pt-2">
          <div className="flex justify-between text-[10px] font-mono text-arkhe-muted mb-1 uppercase">
            <span>Manifestation Progress</span>
            <span>{astl.manifestationProgress.toFixed(1)}%</span>
          </div>
          <div className="h-2 bg-black rounded-full overflow-hidden border border-arkhe-border">
            <div 
              className={`h-full transition-all duration-500 ${isManifestable ? 'bg-arkhe-green shadow-[0_0_10px_rgba(34,197,94,0.5)]' : 'bg-arkhe-orange'}`}
              style={{ width: `${astl.manifestationProgress}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
