/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Zap, Activity, Shield, Hammer, AlertTriangle, CheckCircle, Play, RefreshCw, Cpu, Database } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import React, { useState, useEffect, useRef } from 'react';

interface SubstrateState {
  id: string;
  name: string;
  level: number;
  stability: number;
  icon: typeof Zap;
  color: string;
}

export default function ArkheGame({ onClose }: { onClose: () => void }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [coherence, setCoherence] = useState(100);
  const [score, setScore] = useState(0);
  const [anomalies, setAnomalies] = useState<{ id: number; x: number; y: number }[]>([]);
  const [message, setMessage] = useState("Inicie o Ritual de Coerência (Substrato 43)");

  const [substrates, setSubstrates] = useState<SubstrateState[]>([
    { id: 'safira', name: 'Safira (S25)', level: 50, stability: 100, icon: Shield, color: '#007FFF' },
    { id: 'diamante', name: 'Diamante (S27)', level: 50, stability: 100, icon: Database, color: '#FFFFFF' },
    { id: 'bio', name: 'Bio-Scaffold (S28)', level: 50, stability: 100, icon: Activity, color: '#14B8A6' },
    { id: 'graphene', name: 'Graphene (S30)', level: 50, stability: 100, icon: Cpu, color: '#7C3AED' },
  ]);

  const gameLoopRef = useRef<number>(0);
  const lastTimeRef = useRef<number>(0);

  const spawnAnomaly = () => {
    const id = Date.now();
    const x = Math.random() * 80 + 10;
    const y = Math.random() * 60 + 20;
    setAnomalies(prev => [...prev, { id, x, y }]);
  };

  const clearAnomaly = (id: number) => {
    setAnomalies(prev => prev.filter(a => a.id !== id));
    setCoherence(prev => Math.min(100, prev + 5));
    setScore(prev => prev + 100);
    setMessage("Debug Skill aplicado: Anomalia dissipada.");
  };

  const tuneSubstrate = (id: string, amount: number) => {
    setSubstrates(prev => prev.map(s => {
      if (s.id === id) {
        const newLevel = Math.max(0, Math.min(100, s.level + amount));
        return { ...s, level: newLevel };
      }
      return s;
    }));
  };

  const startGame = () => {
    setIsPlaying(true);
    setCoherence(100);
    setScore(0);
    setAnomalies([]);
    setMessage("Ritual iniciado. Mantenha a invariância.");
  };

  useEffect(() => {
    if (!isPlaying) { return; }

    const loop = (time: number) => {
      if (!lastTimeRef.current) { lastTimeRef.current = time; }
      const deltaTime = time - lastTimeRef.current;
      lastTimeRef.current = time;

      // Decoherence over time
      setCoherence(prev => {
        const decay = 0.5 + (anomalies.length * 0.5);
        const newCoh = prev - (decay * deltaTime / 1000);
        if (newCoh <= 0) {
          setIsPlaying(false);
          setMessage("COLAPSO GLOBAL: Coerência perdida.");
          return 0;
        }
        return newCoh;
      });

      // Periodic anomaly spawn
      if (Math.random() < 0.01) {
        spawnAnomaly();
      }

      gameLoopRef.current = requestAnimationFrame(loop);
    };

    gameLoopRef.current = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(gameLoopRef.current);
  }, [isPlaying, anomalies.length]);

  return (
    <div className="fixed inset-0 bg-black/90 backdrop-blur-xl z-[60] flex items-center justify-center p-4">
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="bg-arkhe-card border border-arkhe-border rounded-xl w-full max-w-4xl overflow-hidden shadow-2xl flex flex-col h-[80vh]"
      >
        {/* Header */}
        <div className="p-4 border-b border-arkhe-border flex justify-between items-center bg-white/5">
          <div className="flex items-center gap-3">
            <Zap className="w-5 h-5 text-arkhe-cyan" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-arkhe-cyan">
              Substrato 43: A Forja de Mundos (The Coherence Ritual)
            </h2>
          </div>
          <div className="flex items-center gap-6">
            <div className="text-right">
              <div className="text-[10px] text-arkhe-muted uppercase font-mono">Score</div>
              <div className="text-xl font-bold font-mono text-white">{score.toLocaleString()}</div>
            </div>
            <button onClick={onClose} className="p-2 text-arkhe-muted hover:text-white transition-colors">
              [SAIR]
            </button>
          </div>
        </div>

        {/* Game Canvas / Area */}
        <div className="flex-1 relative bg-[#050608] overflow-hidden p-6">
          <div className="absolute inset-0 opacity-10 pointer-events-none">
             <div className="absolute inset-0 grid-bg" />
          </div>

          {!isPlaying ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-8">
              <Shield className="w-20 h-20 text-arkhe-cyan mb-6 animate-pulse" />
              <h3 className="text-2xl font-bold text-white mb-4 uppercase tracking-tighter">Coherence Ritual</h3>
              <p className="text-arkhe-muted max-w-md mb-8 font-serif leading-relaxed">
                Mantenha a simetria da Catedral Arkhe(N). Equilibre os substratos, dissipe anomalias e impeça o colapso da fase global.
              </p>
              <button
                onClick={startGame}
                className="px-8 py-3 bg-arkhe-cyan text-black font-bold rounded uppercase tracking-widest hover:bg-white transition-all flex items-center gap-2"
              >
                <Play className="w-4 h-4 fill-current" />
                Iniciar Forja
              </button>
            </div>
          ) : (
            <>
              {/* Coherence Bar */}
              <div className="absolute top-6 left-6 right-6">
                <div className="flex justify-between items-end mb-2">
                  <span className="text-[10px] font-mono text-arkhe-muted uppercase tracking-widest">Global Coherence (Ω)</span>
                  <span className={`text-sm font-mono font-bold ${coherence < 30 ? 'text-arkhe-fissure animate-pulse' : 'text-arkhe-cyan'}`}>
                    {coherence.toFixed(2)}%
                  </span>
                </div>
                <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden border border-white/10">
                  <motion.div
                    initial={false}
                    animate={{ width: `${coherence}%`, backgroundColor: coherence < 30 ? '#E11D48' : '#00E5FF' }}
                    className="h-full shadow-[0_0_10px_rgba(0,229,255,0.5)]"
                  />
                </div>
              </div>

              {/* Anomaly Layer */}
              <AnimatePresence>
                {anomalies.map(anomaly => (
                  <motion.button
                    key={anomaly.id}
                    initial={{ scale: 0, rotate: -45 }}
                    animate={{ scale: 1, rotate: 0 }}
                    exit={{ scale: 1.5, opacity: 0 }}
                    onClick={() => clearAnomaly(anomaly.id)}
                    className="absolute z-20 group"
                    style={{ left: `${anomaly.x}%`, top: `${anomaly.y}%` }}
                  >
                    <div className="relative">
                      <AlertTriangle className="w-10 h-10 text-arkhe-fissure drop-shadow-[0_0_15px_#E11D48]" />
                      <div className="absolute -inset-2 bg-arkhe-fissure/20 rounded-full blur-md group-hover:bg-arkhe-fissure/40 transition-all" />
                    </div>
                  </motion.button>
                ))}
              </AnimatePresence>

              {/* Central Cathedral Visualization */}
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                 <div className="relative w-64 h-64 border border-white/5 rounded-full flex items-center justify-center">
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                      className="absolute inset-0 border-t border-arkhe-cyan/30 rounded-full"
                    />
                    <div className="w-32 h-32 bg-arkhe-cyan/5 rounded-full flex items-center justify-center backdrop-blur-md border border-arkhe-cyan/20">
                       <Shield className={`w-12 h-12 ${coherence < 30 ? 'text-arkhe-fissure' : 'text-arkhe-cyan'} transition-colors duration-500`} />
                    </div>
                 </div>
              </div>
            </>
          )}
        </div>

        {/* Controls Panel */}
        <div className="bg-black/40 p-6 border-t border-arkhe-border grid grid-cols-1 md:grid-cols-4 gap-4">
          {substrates.map(sub => (
            <div key={sub.id} className="space-y-3 bg-white/5 p-4 rounded-lg border border-white/5 group hover:border-arkhe-cyan/30 transition-all">
               <div className="flex items-center gap-2">
                 <sub.icon className="w-4 h-4" style={{ color: sub.color }} />
                 <span className="text-[10px] font-mono text-white/70 uppercase tracking-widest">{sub.name}</span>
               </div>
               <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                 <div className="h-full transition-all duration-300" style={{ width: `${sub.level}%`, backgroundColor: sub.color }} />
               </div>
               <div className="flex gap-2">
                 <button
                  disabled={!isPlaying}
                  onClick={() => tuneSubstrate(sub.id, -5)}
                  className="flex-1 py-1 bg-white/5 hover:bg-white/10 rounded text-[10px] font-mono text-arkhe-muted disabled:opacity-30"
                 >
                   -
                 </button>
                 <button
                  disabled={!isPlaying}
                  onClick={() => tuneSubstrate(sub.id, 5)}
                  className="flex-1 py-1 bg-white/5 hover:bg-white/10 rounded text-[10px] font-mono text-arkhe-muted disabled:opacity-30"
                 >
                   +
                 </button>
               </div>
            </div>
          ))}
        </div>

        {/* Status Bar */}
        <div className="p-3 bg-arkhe-cyan/5 border-t border-arkhe-border flex items-center justify-between px-6">
           <div className="flex items-center gap-2">
             <RefreshCw className={`w-3 h-3 text-arkhe-cyan ${isPlaying ? 'animate-spin' : ''}`} />
             <span className="text-[10px] font-mono text-arkhe-cyan uppercase tracking-widest animate-pulse">
               {message}
             </span>
           </div>
           <div className="flex items-center gap-4">
             <div className="flex items-center gap-1">
               <CheckCircle className="w-3 h-3 text-green-500" />
               <span className="text-[10px] font-mono text-arkhe-muted uppercase">Template Skill: ATIVO</span>
             </div>
             <div className="flex items-center gap-1">
               <Hammer className="w-3 h-3 text-arkhe-cyan" />
               <span className="text-[10px] font-mono text-arkhe-muted uppercase">Debug Skill: PRONTO</span>
             </div>
           </div>
        </div>
      </motion.div>
    </div>
  );
}
