
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Zap, Eye, Send, History, Globe } from 'lucide-react';
import React, { useState } from 'react';

import type { SimulationState } from '../../server/types';
import { cn } from '../lib/utils';

import { Card } from './ui/Card';


interface TemporalLensPanelProps {
  state: SimulationState;
}

const TemporalLensPanel: React.FC<TemporalLensPanelProps> = ({ state }) => {
  const [message, setMessage] = useState('');

  const handleSendFeedback = async () => {
    if (!message.trim()) {return;}

    try {
      await fetch('/api/feedback/population', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
      });
      setMessage('');
    } catch (err) {
      console.error("Failed to send feedback", err);
    }
  };

  const handleHandshake = async () => {
    try {
      await fetch('/api/qhttp/retrocausal-handshake', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ payload: 'temporal_scan_2027' })
      });
    } catch (err) {
      console.error("Failed to trigger handshake", err);
    }
  };

  const nare = state.nare;
  const feedback = state.populationFeedback || [];

  return (
    <Card
      title="Lente Temporal: Rio 2027 (NARE-qhttp)"
      icon={<Eye className="text-[#00FFAA] w-4 h-4" />}
      action={
        <div className={cn(
          "px-2 py-0.5 rounded text-[8px] border",
          nare?.epState ? 'bg-[#00FFAA]/10 text-[#00FFAA] border-[#00FFAA]/30' : 'bg-red-500/10 text-red-400 border-red-500/30'
        )}>
          {nare?.status || 'IDLE'}
        </div>
      }
      className="bg-[#0A0E17] border-[#00FFAA]/30"
    >
      <div className="space-y-4">
        {/* NARE Diagnostics */}
        <div className="grid grid-cols-2 gap-4 text-[10px] uppercase tracking-tighter">
          <div className="bg-black/40 p-2 rounded border border-[#00FFAA]/5">
            <div className="text-white/50 mb-1 flex items-center gap-1">
              <Zap className="w-3 h-3 text-[#FF5A1A]" />
              Latência Efetiva
            </div>
            <div className="text-base font-mono text-[#00FFAA]">
              {nare?.avgEffectiveLatencyMs?.toFixed(2)}ms
            </div>
          </div>
          <div className="bg-black/40 p-2 rounded border border-[#00FFAA]/5">
            <div className="text-white/50 mb-1 flex items-center gap-1">
              <History className="w-3 h-3 text-[#00FFAA]" />
              Pre-ACKs
            </div>
            <div className="text-base font-mono text-white">
              {nare?.preAcksSuccess}/{nare?.packetsTransmitted}
            </div>
          </div>
        </div>

        {/* Temporal Visualization (Placeholder) */}
        <div className="h-32 bg-black/60 rounded border border-[#00FFAA]/20 relative overflow-hidden flex items-center justify-center">
          <div className="absolute inset-0 opacity-20 pointer-events-none">
            <div className="h-full w-full" style={{
              backgroundImage: 'radial-gradient(circle, #00FFAA 1px, transparent 1px)',
              backgroundSize: '20px 20px'
            }} />
          </div>
          <div className="text-center z-10">
            <Globe className="w-8 h-8 text-[#00FFAA] mx-auto mb-2 animate-pulse" />
            <div className="text-[10px] text-[#00FFAA]/80 font-mono">
              MALHA URBANA 2027 RENDERIZADA<br />
              λ₂ = {nare?.currentLambda2?.toFixed(4)}
            </div>
          </div>
          <button
            className="absolute bottom-1 right-1 px-2 py-1 bg-[#00FFAA]/10 hover:bg-[#00FFAA]/20 border border-[#00FFAA]/30 text-[#00FFAA] text-[8px] rounded uppercase font-mono transition-colors"
            onClick={handleHandshake}
          >
            HANDSHAKE TEMPORAL
          </button>
        </div>

        {/* Population Feedback */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-[10px] uppercase text-white/50">
            <Send className="w-3 h-3" />
            Feedback Populacional (MaxToki)
          </div>
          <div className="h-32 rounded bg-black/20 p-2 border border-white/5 overflow-y-auto scrollbar-hide">
            {feedback.map((f: unknown) => (
              <div key={f.id} className="mb-3 last:mb-0 text-[11px] leading-tight">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-[#00FFAA] font-bold">{f.residentName} (2027)</span>
                  <span className="text-white/30 text-[9px] font-mono">
                    {new Date(f.timestamp || 0).toLocaleTimeString()}
                  </span>
                </div>
                <p className="text-white/80">{f.message}</p>
                <div className="h-[1px] w-full bg-white/5 mt-1" />
              </div>
            ))}
          </div>
          <div className="flex gap-2">
            <input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Interagir com sua versão 2027..."
              className="flex-1 h-8 px-2 text-[11px] bg-black/40 border border-white/10 rounded focus:border-[#00FFAA]/50 outline-none text-white"
              onKeyDown={(e) => e.key === 'Enter' && handleSendFeedback()}
            />
            <button
              className="h-8 w-8 flex items-center justify-center bg-[#00FFAA] hover:bg-[#00FFAA]/80 text-black rounded transition-colors"
              onClick={handleSendFeedback}
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default TemporalLensPanel;
