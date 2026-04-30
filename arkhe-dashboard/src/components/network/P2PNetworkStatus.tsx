
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// arkhe-dashboard/src/components/network/P2PNetworkStatus.tsx
'use client';

import { useState } from 'react';

import { peerMesh } from '@/lib/webrtc/peerMesh';

export default function P2PNetworkStatus() {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [metrics, _setMetrics] = useState<any>(peerMesh.getAggregatedMetrics());

  return (
    <div className="bg-black/40 border border-green-500/20 rounded-3xl p-6">
      <h3 className="text-sm font-bold text-green-400 mb-4 flex items-center gap-2">
        <span className="text-lg">🌐</span> MALHA P2P BIOFEEDBACK
      </h3>
      <div className="space-y-3 mb-6">
        <div className="flex justify-between text-[10px]">
          <span className="text-slate-500">NÓS CONECTADOS</span>
          <span className="text-cyan-400 font-mono">{metrics.nodeCount}</span>
        </div>
        <div className="flex justify-between text-[10px]">
          <span className="text-slate-500">Ω MÉDIO MALHA</span>
          <span className="text-purple-400 font-mono">{metrics.avgOmega.toFixed(4)}</span>
        </div>
      </div>
      <div className="p-3 bg-white/5 rounded-xl border border-white/5 text-[8px] text-slate-500 font-mono italic">
        Sincronização via WebRTC DataChannels ativa. Estado de coerência propagado por gossip ético.
      </div>
    </div>
  );
}
