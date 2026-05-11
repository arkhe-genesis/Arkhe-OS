/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Activity, Zap, Network } from 'lucide-react';
import React, { useState, useEffect, useRef } from 'react';

interface ArkheGridSimulatorProps {
  onClose: () => void;
}

export default function ArkheGridSimulator({ onClose }: ArkheGridSimulatorProps) {
  const [volatility, setVolatility] = useState(40);
  const [noise, setNoise] = useState(50);
  const [coupling, setCoupling] = useState(0.2);
  const [coherence, setCoherence] = useState(0);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const requestRef = useRef<number | undefined>(undefined);
  


  // Physics state
  const N = 8;
  const phasesRef = useRef<number[]>(Array(N).fill(0).map(() => Math.random() * Math.PI * 2));
  const baseOffsetsRef = useRef<number[]>(Array(N).fill(0).map(() => (Math.random() - 0.5) * 2));

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) {return;}
    const ctx = canvas.getContext('2d');
    if (!ctx) {return;}

    let time = 0;
    const dt = 0.016; // ~60fps
    const baseFreq = 2.0; // Visual base frequency

    const render = () => {
      time += dt;

      // Update Physics (Kuramoto Model)
      const phases = phasesRef.current;
      const newPhases = [...phases];
      let sumCos = 0;
      let sumSin = 0;

      for (let i = 0; i < N; i++) {
        let sumCoupling = 0;
        for (let j = 0; j < N; j++) {
          sumCoupling += Math.sin(phases[j] - phases[i]);
        }

        const noiseFactor = (noise / 100) * (Math.random() - 0.5) * 5.0;
        const volFactor = (volatility / 100) * baseOffsetsRef.current[i] * 3.0;
        const w_i = baseFreq + volFactor + noiseFactor;

        newPhases[i] += (w_i + (coupling / N) * sumCoupling) * dt;

        sumCos += Math.cos(newPhases[i]);
        sumSin += Math.sin(newPhases[i]);
      }

      phasesRef.current = newPhases;
      const R = Math.sqrt(sumCos * sumCos + sumSin * sumSin) / N;
      setCoherence(R);

      // Draw
      const width = canvas.width;
      const height = canvas.height;
      ctx.clearRect(0, 0, width, height);

      const centerX = width / 2;
      const centerY = height / 2 - 40;
      const radius = 120;

      // Draw connections
      ctx.lineWidth = 2;
      for (let i = 0; i < N; i++) {
        const angle = (i / N) * Math.PI * 2;
        const x = centerX + Math.cos(angle) * radius;
        const y = centerY + Math.sin(angle) * radius;

        // Color based on alignment with global phase
        const globalPhase = Math.atan2(sumSin, sumCos);
        const phaseDiff = Math.abs(Math.sin((newPhases[i] - globalPhase) / 2));

        if (R > 0.8) {
          ctx.strokeStyle = `rgba(0, 255, 255, ${0.2 + 0.8 * R})`;
        } else {
          ctx.strokeStyle = `rgba(255, ${Math.floor(100 * (1-phaseDiff))}, 0, 0.5)`;
        }

        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(x, y);
        ctx.stroke();
      }

      // Draw central hub
      ctx.beginPath();
      ctx.arc(centerX, centerY, 20, 0, Math.PI * 2);
      ctx.fillStyle = R > 0.8 ? '#00ffff' : '#ff4400';
      ctx.fill();
      ctx.shadowBlur = 15;
      ctx.shadowColor = R > 0.8 ? '#00ffff' : '#ff4400';
      ctx.fill();
      ctx.shadowBlur = 0;

      // Draw nodes
      for (let i = 0; i < N; i++) {
        const angle = (i / N) * Math.PI * 2;
        const x = centerX + Math.cos(angle) * radius;
        const y = centerY + Math.sin(angle) * radius;

        ctx.beginPath();
        ctx.arc(x, y, 15, 0, Math.PI * 2);
        ctx.fillStyle = '#111214';
        ctx.fill();
        ctx.strokeStyle = R > 0.8 ? '#00ffff' : '#ff4400';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Draw mini sine wave inside node
        ctx.beginPath();
        for (let px = -10; px <= 10; px++) {
          const py = Math.sin(px * 0.5 - newPhases[i]) * 8;
          if (px === -10) {ctx.moveTo(x + px, y + py);}
          else {ctx.lineTo(x + px, y + py);}
        }
        ctx.strokeStyle = R > 0.8 ? '#00ffff' : '#ff8800';
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      // Draw aggregate grid frequency at the bottom
      const waveY = height - 60;

      // We'll draw a wave that represents the aggregate signal
      // If R is high, it's a clean sine wave. If R is low, it's messy.
      ctx.beginPath();
      for (let x = 0; x < width; x++) {
        let y = 0;
        const t = time * 5 - (x * 0.05);

        if (R > 0.8) {
          // Clean 60Hz-like wave
          y = Math.sin(t) * 30;
        } else {
          // Messy wave from individual phases
          for (let i = 0; i < N; i++) {
            y += Math.sin(t + newPhases[i]) * (30 / N);
          }
        }

        if (x === 0) {
          ctx.moveTo(x, waveY + y);
        } else {
          ctx.lineTo(x, waveY + y);
        }
      }

      ctx.strokeStyle = R > 0.8 ? '#00ffff' : '#ff4400';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Draw target 60Hz line faintly
      ctx.beginPath();
      for (let x = 0; x < width; x++) {
        const t = time * 5 - (x * 0.05);
        if (x === 0) {
          ctx.moveTo(x, waveY + Math.sin(t) * 30);
        } else {
          ctx.lineTo(x, waveY + Math.sin(t) * 30);
        }
      }
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
      ctx.lineWidth = 1;
      ctx.stroke();

      requestRef.current = requestAnimationFrame(render);
    };

    requestRef.current = requestAnimationFrame(render);
    return () => {
      if (requestRef.current) {cancelAnimationFrame(requestRef.current);}
    };
  }, [volatility, noise, coupling]);

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#111214] border border-[#1f2024] rounded-xl w-full max-w-5xl h-[700px] flex flex-col overflow-hidden shadow-2xl">
        <div className="flex items-center justify-between p-4 border-b border-[#1f2024] bg-black/20">
          <div className="flex items-center gap-3">
            <Zap className="w-5 h-5 text-arkhe-cyan" />
            <h2 className="font-mono text-lg uppercase tracking-widest text-arkhe-cyan">Arkhe-Grid: Energy Phase Sync</h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 flex flex-col md:flex-row">
          {/* Left Panel: Controls */}
          <div className="w-full md:w-80 border-r border-[#1f2024] p-6 flex flex-col gap-8 bg-black/10 overflow-y-auto">
            <div>
              <h3 className="text-xs font-mono uppercase tracking-widest text-arkhe-muted mb-4">Grid Parameters</h3>

              <div className="space-y-6">
                <div>
                  <div className="flex justify-between text-xs font-mono mb-2">
                    <span className="text-arkhe-text">Load Volatility</span>
                    <span className="text-arkhe-orange">{volatility}%</span>
                  </div>
                  <input
                    type="range"
                    min="0" max="100"
                    value={volatility}
                    onChange={(e) => setVolatility(Number(e.target.value))}
                    className="w-full accent-arkhe-orange"
                  />
                  <p className="text-[10px] text-arkhe-muted mt-1 font-mono">Simulates sudden demand spikes (AC drift).</p>
                </div>

                <div>
                  <div className="flex justify-between text-xs font-mono mb-2">
                    <span className="text-arkhe-text">Renewable Noise</span>
                    <span className="text-arkhe-orange">{noise}%</span>
                  </div>
                  <input
                    type="range"
                    min="0" max="100"
                    value={noise}
                    onChange={(e) => setNoise(Number(e.target.value))}
                    className="w-full accent-arkhe-orange"
                  />
                  <p className="text-[10px] text-arkhe-muted mt-1 font-mono">Simulates solar/wind injection jitter.</p>
                </div>

                <div className="pt-4 border-t border-[#1f2024]">
                  <div className="flex justify-between text-xs font-mono mb-2">
                    <span className="text-arkhe-cyan font-bold">Kuramoto Coupling (K)</span>
                    <span className="text-arkhe-cyan">{coupling.toFixed(2)}</span>
                  </div>
                  <input
                    type="range"
                    min="0" max="2" step="0.01"
                    value={coupling}
                    onChange={(e) => setCoupling(Number(e.target.value))}
                    className="w-full accent-arkhe-cyan"
                  />
                  <p className="text-[10px] text-arkhe-muted mt-1 font-mono">Arkhe phase-lock enforcement strength.</p>
                </div>
              </div>
            </div>

            <div className="mt-auto">
              <div className={`p-4 rounded-lg border ${coherence > 0.8 ? 'bg-arkhe-cyan/10 border-arkhe-cyan/30' : 'bg-arkhe-red/10 border-arkhe-red/30'}`}>
                <div className="text-xs font-mono uppercase tracking-widest text-arkhe-muted mb-1">Grid Coherence (Ω)</div>
                <div className={`text-3xl font-bold font-mono ${coherence > 0.8 ? 'text-arkhe-cyan' : 'text-arkhe-red'}`}>
                  {coherence.toFixed(3)}
                </div>
                <div className="text-[10px] font-mono mt-2 uppercase tracking-wider opacity-70">
                  {coherence > 0.8 ? 'Phase-Locked (Stable 60Hz)' : 'Decoherence Risk (Blackout Imminent)'}
                </div>
              </div>
            </div>
          </div>

          {/* Right Panel: Visualization */}
          <div className="flex-1 relative bg-[#0a0a0c] flex flex-col">
            <div className="absolute top-4 left-4 flex gap-4">
              <div className="flex items-center gap-2 text-xs font-mono text-arkhe-muted">
                <Network className="w-4 h-4" />
                <span>Microgrid Nodes: {N}</span>
              </div>
              <div className="flex items-center gap-2 text-xs font-mono text-arkhe-muted">
                <Activity className="w-4 h-4" />
                <span>Target: 60.00 Hz</span>
              </div>
            </div>

            <div className="flex-1 flex items-center justify-center p-4">
              <canvas
                ref={canvasRef}
                width={600}
                height={500}
                className="max-w-full max-h-full"
              />
            </div>

            <div className="absolute bottom-4 left-4 right-4 text-center text-[10px] font-mono text-arkhe-muted uppercase tracking-widest">
              Aggregate Grid Frequency (AC)
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
