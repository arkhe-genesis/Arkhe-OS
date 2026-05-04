
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// arkhe-dashboard/src/components/meditation/CoherentMeditationPanel.tsx
'use client';

import {useState, useEffect, useRef} from 'react';

export default function CoherentMeditationPanel() {
  const [isMeditating, setIsMeditating] = useState(false);
  const [collectiveOmega, setCollectiveOmega] = useState(0.9);
  const [collectiveCoherence, setCollectiveCoherence] = useState(0.0);
  const [binauralFrequency, setBinauralFrequency] = useState(10.0);
  const [participantCount, setParticipantCount] = useState(1);

  const audioContextRef = useRef<AudioContext | null>(null);

  useEffect(() => {
    const initAudio = async () => {
      if (typeof window !== 'undefined' && 'AudioContext' in window) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        audioContextRef.current = new (window as any).AudioContext();
      }
    };
    void initAudio();

    return () => {
      if (audioContextRef.current) {
        void audioContextRef.current.close();
      }
    };
  }, []);

  const startMeditation = () => {
    setIsMeditating(true);
    setParticipantCount(Math.floor(Math.random() * 10) + 5);
  };

  const endMeditation = () => {
    setIsMeditating(false);
  };

  useEffect(() => {
    if (!isMeditating) {return;}

    const interval = setInterval(() => {
      setCollectiveCoherence(prev =>
        Math.min(1.0, prev + 0.05 * Math.random()),
      );
      setCollectiveOmega(prev => Math.min(0.98, prev + 0.01 * Math.random()));
      setBinauralFrequency(8 + Math.random() * 10);
    }, 2000);

    return () => clearInterval(interval);
  }, [isMeditating]);

  return (
    <div className="bg-black/30 rounded-2xl border border-emerald-500/20 p-4">
      <h3 className="text-xs font-bold text-emerald-400 mb-3 tracking-widest uppercase flex items-center gap-2">
        <span>🧘</span> Coherent Meditation
      </h3>

      <div className="flex gap-2 mb-4">
        {!isMeditating ? (
          <button
            onClick={startMeditation}
            className="flex-1 py-2 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-lg text-[10px] font-bold hover:bg-emerald-500/20 transition"
          >
            START MEDITATION
          </button>
        ) : (
          <button
            onClick={endMeditation}
            className="flex-1 py-2 bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg text-[10px] font-bold hover:bg-red-500/20 transition"
          >
            END SESSION
          </button>
        )}
      </div>

      {isMeditating && (
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-[10px] text-slate-500">COLLECTIVE Ω</span>
            <span className="text-[10px] font-mono text-cyan-400">
              {collectiveOmega.toFixed(3)}
            </span>
          </div>

          <div className="flex justify-between items-center">
            <span className="text-[10px] text-slate-500">COHERENCE</span>
            <span className="text-[10px] font-mono text-purple-400">
              {(collectiveCoherence * 100).toFixed(1)}%
            </span>
          </div>

          <div className="flex justify-between items-center">
            <span className="text-[10px] text-slate-500">BINAURAL</span>
            <span className="text-[10px] font-mono text-amber-400">
              {binauralFrequency.toFixed(1)} Hz
            </span>
          </div>

          <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500 transition-all duration-500"
              style={{width: `${collectiveCoherence * 100}%`}}
            />
          </div>

          <p className="text-[9px] text-emerald-500/60 text-center font-mono">
            {participantCount} BODIES IN RESONANCE
          </p>
        </div>
      )}
    </div>
  );
}
