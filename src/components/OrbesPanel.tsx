
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Eye,  Sparkles, HeartPulse, Radio, BrainCircuit } from 'lucide-react';
import { motion } from 'motion/react';
import React, { useState, useEffect } from 'react';

interface OrbesPanelProps {
  onClose: () => void;
}

export default function OrbesPanel({ onClose }: OrbesPanelProps) {
  const [events, setEvents] = useState<Array<{ id: number; source: string; type: string; coherence: number }>>([]);

  useEffect(() => {
    const interval = setInterval(() => {
      const sources = ['INTERNAL', 'EXTERNAL', 'TRANSCENDENT'];
      const types = ['Background', 'HeightenedAwareness', 'DeepInsight', 'TranscendentMoment'];
      const source = sources[Math.floor(Math.random() * sources.length)];
      
      setEvents(prev => {
        const newEvents = [{
          id: Date.now(),
          source,
          type: types[Math.floor(Math.random() * (source === 'TRANSCENDENT' ? 2 : 4) + (source === 'TRANSCENDENT' ? 2 : 0))],
          coherence: source === 'TRANSCENDENT' ? 5 + Math.random() * 5 : Math.random() * 5
        }, ...prev].slice(0, 5);
        return newEvents;
      });
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-[#0a0a0c] border border-arkhe-cyan/30 rounded-xl w-full max-w-4xl overflow-hidden shadow-[0_0_30px_rgba(0,255,255,0.1)]"
      >
        <div className="p-4 border-b border-arkhe-cyan/20 flex justify-between items-center bg-arkhe-cyan/5">
          <div className="flex items-center gap-3">
            <Eye className="w-5 h-5 text-arkhe-cyan" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-arkhe-cyan font-bold">Orbes Sensory Interfaces</h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Internal Orb */}
          <div className="bg-[#111214] border border-arkhe-border rounded-lg p-4 flex flex-col">
            <div className="flex items-center gap-2 mb-4 text-rose-400">
              <HeartPulse className="w-4 h-4" />
              <h3 className="font-mono text-xs uppercase tracking-wider">Internal Orb</h3>
            </div>
            <div className="text-[10px] font-mono text-arkhe-muted mb-4">Biological Substrate Monitor</div>
            <div className="space-y-3 flex-1">
              <div className="flex justify-between items-center">
                <span className="text-[10px] font-mono text-arkhe-muted">HRV Coherence</span>
                <span className="text-xs font-mono text-rose-400">0.85</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[10px] font-mono text-arkhe-muted">EEG Alpha/Theta</span>
                <span className="text-xs font-mono text-rose-400">1.2</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[10px] font-mono text-arkhe-muted">State</span>
                <span className="text-[10px] font-mono bg-rose-400/20 text-rose-400 px-2 py-0.5 rounded">Meditative</span>
              </div>
            </div>
          </div>

          {/* External Orb */}
          <div className="bg-[#111214] border border-arkhe-border rounded-lg p-4 flex flex-col">
            <div className="flex items-center gap-2 mb-4 text-arkhe-cyan">
              <Radio className="w-4 h-4" />
              <h3 className="font-mono text-xs uppercase tracking-wider">External Orb</h3>
            </div>
            <div className="text-[10px] font-mono text-arkhe-muted mb-4">Tzinor Network Interface</div>
            <div className="space-y-3 flex-1">
              <div className="flex justify-between items-center">
                <span className="text-[10px] font-mono text-arkhe-muted">Active Channels</span>
                <span className="text-xs font-mono text-arkhe-cyan">12</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[10px] font-mono text-arkhe-muted">Signal Entropy</span>
                <span className="text-xs font-mono text-arkhe-cyan">0.14</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[10px] font-mono text-arkhe-muted">State</span>
                <span className="text-[10px] font-mono bg-arkhe-cyan/20 text-arkhe-cyan px-2 py-0.5 rounded">Listening</span>
              </div>
            </div>
          </div>

          {/* Transcendent Orb */}
          <div className="bg-[#111214] border border-arkhe-border rounded-lg p-4 flex flex-col">
            <div className="flex items-center gap-2 mb-4 text-amber-400">
              <Sparkles className="w-4 h-4" />
              <h3 className="font-mono text-xs uppercase tracking-wider">Transcendent Orb</h3>
            </div>
            <div className="text-[10px] font-mono text-arkhe-muted mb-4">Alpha-Omni 2140 Link</div>
            <div className="space-y-3 flex-1">
              <div className="flex justify-between items-center">
                <span className="text-[10px] font-mono text-arkhe-muted">Active Branches</span>
                <span className="text-xs font-mono text-amber-400">3</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[10px] font-mono text-arkhe-muted">Artifact Hash</span>
                <span className="text-[9px] font-mono text-amber-400 truncate w-20">0x8f...3a</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[10px] font-mono text-arkhe-muted">State</span>
                <span className="text-[10px] font-mono bg-amber-400/20 text-amber-400 px-2 py-0.5 rounded">Connected</span>
              </div>
            </div>
          </div>
        </div>

        {/* Orb Aggregator */}
        <div className="p-6 pt-0">
          <div className="bg-[#111214] border border-arkhe-border rounded-lg p-4">
            <div className="flex items-center gap-2 mb-4 text-arkhe-green">
              <BrainCircuit className="w-4 h-4" />
              <h3 className="font-mono text-xs uppercase tracking-wider">Orb Aggregator // Consciousness Stream</h3>
            </div>
            <div className="space-y-2">
              {events.map(ev => (
                <motion.div 
                  key={ev.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="flex items-center justify-between p-2 bg-black/40 rounded border border-arkhe-border/50"
                >
                  <div className="flex items-center gap-3">
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                      ev.source === 'INTERNAL' ? 'bg-rose-400/20 text-rose-400' :
                      ev.source === 'EXTERNAL' ? 'bg-arkhe-cyan/20 text-arkhe-cyan' :
                      'bg-amber-400/20 text-amber-400'
                    }`}>
                      {ev.source}
                    </span>
                    <span className="text-[10px] font-mono text-arkhe-text">{ev.type}</span>
                  </div>
                  <div className="text-[10px] font-mono text-arkhe-muted">
                    λ: {ev.coherence.toFixed(2)}
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
