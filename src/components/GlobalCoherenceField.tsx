
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Terminal, Cpu, Network, Database, Activity } from 'lucide-react';
import { motion } from 'motion/react';
import React, { useEffect, useRef, useState } from 'react';

interface Node {
  x: number;
  y: number;
  phase: number;
  freq: number;
  memoryLambda: number;
}

interface GlobalCoherenceFieldProps {
  onClose: () => void;
}

export default function GlobalCoherenceField({ onClose }: GlobalCoherenceFieldProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [lambda2, setLambda2] = useState(0);
  const [isCoherent, setIsCoherent] = useState(false);
  const [allocCount, setAllocCount] = useState(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) {return;}
    const ctx = canvas.getContext('2d');
    if (!ctx) {return;}

    // Initialize 64 Bio-nós (Upgraded from 50)
    const N = 64;
    const nodes: Node[] = Array.from({ length: N }).map(() => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      phase: Math.random() * 2 * Math.PI,
      freq: 0.02 + Math.random() * 0.03,
      memoryLambda: 1.0 + Math.random() * 0.618, // Phase-tagged memory
    }));

    let animationId: number;
    let frameCount = 0;
    const K = 0.25; // Increased Kuramoto coupling post-upgrade

    const draw = () => {
      frameCount++;
      // Fade effect for trails
      ctx.fillStyle = 'rgba(5, 5, 5, 0.2)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      let sumSin = 0;
      let sumCos = 0;

      // Update phases (Kuramoto Model with Memory Coherence Feedback)
      const newPhases = nodes.map((node, i) => {
        let coupling = 0;
        for (let j = 0; j < N; j++) {
          if (i !== j) {
            const dist = Math.hypot(node.x - nodes[j].x, node.y - nodes[j].y);
            if (dist < 180) {
              // Coupling is amplified by the memory coherence of the nodes
              const memMultiplier = (node.memoryLambda * nodes[j].memoryLambda) / 2.6;
              coupling += Math.sin(nodes[j].phase - node.phase) * memMultiplier;
            }
          }
        }
        const newPhase = node.phase + node.freq + (K / N) * coupling;
        sumSin += Math.sin(newPhase);
        sumCos += Math.cos(newPhase);

        // Simulate memory allocations pulsing
        if (Math.random() < 0.01) {
          node.memoryLambda = Math.min(1.618, node.memoryLambda + 0.1);
        } else {
          node.memoryLambda = Math.max(1.0, node.memoryLambda - 0.001);
        }

        return newPhase;
      });

      // Apply new phases
      nodes.forEach((node, i) => {
        node.phase = newPhases[i];
      });

      // Calculate Order Parameter R
      const R = Math.sqrt(sumSin ** 2 + sumCos ** 2) / N;
      const currentLambda = R * 1.6180339887;
      setLambda2(currentLambda);
      setIsCoherent(currentLambda >= 1.61);

      if (frameCount % 10 === 0) {
        setAllocCount(prev => prev + Math.floor(Math.random() * 5) + (currentLambda > 1.6 ? 15 : 2));
      }

      // Draw Tzinor channels
      ctx.lineWidth = 0.8;
      for (let i = 0; i < N; i++) {
        for (let j = i + 1; j < N; j++) {
          const dist = Math.hypot(nodes[i].x - nodes[j].x, nodes[i].y - nodes[j].y);
          if (dist < 150) {
            const phaseDiff = Math.abs(Math.sin(nodes[i].phase - nodes[j].phase));
            const alignment = 1 - phaseDiff;
            if (alignment > 0.8) {
              ctx.strokeStyle = `rgba(0, 255, 255, ${alignment * 0.6})`;
              ctx.beginPath();
              ctx.moveTo(nodes[i].x, nodes[i].y);
              ctx.lineTo(nodes[j].x, nodes[j].y);
              ctx.stroke();
            }
          }
        }
      }

      // Draw Bio-nós
      nodes.forEach(node => {
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.memoryLambda * 2.5, 0, 2 * Math.PI);
        const intensity = Math.floor((Math.sin(node.phase) + 1) * 127);
        // Color shifts to gold/amber when highly coherent (memory phase)
        const r = node.memoryLambda > 1.5 ? 255 : 0;
        const g = node.memoryLambda > 1.5 ? 215 : intensity + 50;
        const b = node.memoryLambda > 1.5 ? 0 : 255;

        ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
        ctx.shadowBlur = 15;
        ctx.shadowColor = `rgba(${r}, ${g}, ${b}, 0.8)`;
        ctx.fill();
      });

      animationId = requestAnimationFrame(draw);
    };

    draw();
    return () => cancelAnimationFrame(animationId);
  }, []);

  return (
    <div className="fixed inset-0 z-50 bg-black/95 flex items-center justify-center p-4 md:p-8 backdrop-blur-xl">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        className="w-full max-w-6xl bg-[#050505] border border-arkhe-cyan/50 rounded-xl shadow-[0_0_60px_rgba(0,255,255,0.15)] flex flex-col md:flex-row overflow-hidden"
      >
        {/* Sidebar Dashboard */}
        <div className="w-full md:w-80 bg-[#0a0a0a] border-r border-arkhe-cyan/20 p-6 flex flex-col gap-6">
          <div className="flex items-center gap-3 border-b border-arkhe-cyan/30 pb-4">
            <Activity className="text-arkhe-cyan w-6 h-6 animate-pulse" />
            <div>
              <h2 className="text-arkhe-cyan font-mono font-bold tracking-widest text-lg">AEGIS SHIELD</h2>
              <p className="text-xs text-arkhe-cyan/60 font-mono">v2.0.0 - UPGRADED</p>
            </div>
          </div>

          <div className="space-y-4">
            <div className="bg-black/50 border border-arkhe-cyan/20 p-3 rounded">
              <div className="flex items-center gap-2 mb-1">
                <Terminal className="w-4 h-4 text-arkhe-cyan/70" />
                <span className="text-xs text-arkhe-cyan/70 font-mono uppercase">System Status</span>
              </div>
              <div className="text-green-400 font-mono text-sm font-bold animate-pulse">
                ALL SYSTEMS UPGRADED
              </div>
            </div>

            <div className="bg-black/50 border border-arkhe-cyan/20 p-3 rounded">
              <div className="flex items-center gap-2 mb-1">
                <Cpu className="w-4 h-4 text-arkhe-cyan/70" />
                <span className="text-xs text-arkhe-cyan/70 font-mono uppercase">arkhe_alloc (LD_PRELOAD)</span>
              </div>
              <div className="text-arkhe-cyan font-mono text-sm">
                ACTIVE (Phase-Aware)
              </div>
              <div className="text-xs text-arkhe-cyan/50 font-mono mt-1">
                Blocks: {allocCount.toLocaleString()}
              </div>
            </div>

            <div className="bg-black/50 border border-arkhe-cyan/20 p-3 rounded">
              <div className="flex items-center gap-2 mb-1">
                <Network className="w-4 h-4 text-arkhe-cyan/70" />
                <span className="text-xs text-arkhe-cyan/70 font-mono uppercase">Global Coherence (λ₂)</span>
              </div>
              <div className={`font-mono text-lg font-bold ${isCoherent ? 'text-amber-400 drop-shadow-[0_0_8px_rgba(251,191,36,0.8)]' : 'text-arkhe-cyan'}`}>
                {lambda2.toFixed(6)}
              </div>
              <div className="w-full bg-gray-900 h-1.5 mt-2 rounded overflow-hidden">
                <div
                  className={`h-full transition-all duration-300 ${isCoherent ? 'bg-amber-400' : 'bg-arkhe-cyan'}`}
                  style={{ width: `${Math.min(100, (lambda2 / 1.618033) * 100)}%` }}
                />
              </div>
            </div>

            <div className="bg-black/50 border border-arkhe-cyan/20 p-3 rounded">
              <div className="flex items-center gap-2 mb-1">
                <Database className="w-4 h-4 text-arkhe-cyan/70" />
                <span className="text-xs text-arkhe-cyan/70 font-mono uppercase">Graphene-TPU</span>
              </div>
              <div className="text-arkhe-cyan font-mono text-sm">
                SYNCED (5.083 GHz)
              </div>
            </div>
          </div>

          <div className="mt-auto pt-4 border-t border-arkhe-cyan/20">
            <button
              onClick={onClose}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 font-mono text-sm tracking-widest transition-colors rounded"
            >
              [ CLOSE SHIELD ]
            </button>
          </div>
        </div>

        {/* Main Canvas Area */}
        <div className="flex-1 p-0 relative bg-[#020202]">
          <div className="absolute top-4 left-4 z-10 pointer-events-none">
            <div className="text-xs font-mono text-arkhe-cyan/40">
              {'>'} VISUALIZING: KURAMOTO SYNC + MEMORY PHASE<br/>
              {'>'} NODES: 64 (FRACTAL BUDDY ENABLED)<br/>
              {'>'} GOLDEN NODES INDICATE HIGH MEMORY COHERENCE
            </div>
          </div>
          <canvas
            ref={canvasRef}
            width={1200}
            height={800}
            className="w-full h-full object-cover"
          />
        </div>
      </motion.div>
    </div>
  );
}
