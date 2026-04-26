
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, HeartPulse, Activity, Fingerprint, Waves, BrainCircuit } from 'lucide-react';
import { motion } from 'motion/react';
import React, { useState, useEffect } from 'react';

interface NeuralMolecularBridgePanelProps {
  onClose: () => void;
}

interface ConsciousnessPayload {
  nodeId: string;
  heartRate: number;
  hrvSdnn: number;
  lfHfRatio: number;
  phiIit: number;
  coherenceIndex: number;
  timestamp: number;
  rawEntropy: string;
}

export default function NeuralMolecularBridgePanel({ onClose }: NeuralMolecularBridgePanelProps) {
  const [payloads, setPayloads] = useState<ConsciousnessPayload[]>([]);
  const [isConnected, setIsConnected] = useState(true);

  // Simulate incoming gRPC stream from the iOS/watchOS app
  useEffect(() => {
    if (!isConnected) {return;}

    const interval = setInterval(() => {
      // Generate stochastic biological data
      const baseHR = 65 + Math.sin(Date.now() / 5000) * 10;
      const stochasticNoise = (Math.random() - 0.5) * 5;
      const hr = baseHR + stochasticNoise;

      const hrv = 40 + Math.random() * 20 + Math.sin(Date.now() / 10000) * 15;

      // LF/HF Ratio (Autonomic Balance)
      const lfHf = 0.8 + Math.random() * 1.4;

      // Integrated Information Theory (Φ) metric proxy
      const lfPower = hrv * hrv * 0.6;
      const hfPower = hrv * hrv * 0.4;
      const complexity = (lfPower + hfPower) / (Math.abs(lfPower - hfPower) + 1.0);
      const phi = Math.log(complexity + 1.0);

      // Collective Coherence from LF/HF balance
      const coherence = 1.618 * (1.0 + Math.atan(lfHf - 1.0) / Math.PI);

      const newPayload: ConsciousnessPayload = {
        nodeId: 'ios-bridge-7a9f',
        heartRate: hr,
        hrvSdnn: hrv,
        lfHfRatio: lfHf,
        phiIit: phi,
        coherenceIndex: coherence,
        timestamp: Date.now(),
        rawEntropy: Array.from({ length: 8 }, () => Math.floor(Math.random() * 256).toString(16).padStart(2, '0')).join(''),
      };

      setPayloads(prev => [newPayload, ...prev].slice(0, 10)); // Keep last 10
    }, 1000); // 1Hz sampling rate

    return () => clearInterval(interval);
  }, [isConnected]);

  const latest = payloads[0];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-[#0a0a0c] border border-rose-500/50 rounded-xl w-full max-w-6xl h-[85vh] flex flex-col overflow-hidden shadow-[0_0_30px_rgba(244,63,94,0.15)]"
      >
        <div className="flex items-center justify-between p-4 border-b border-rose-500/20 bg-rose-500/5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-rose-500/20 rounded-lg">
              <BrainCircuit className="w-5 h-5 text-rose-400" />
            </div>
            <div>
              <h2 className="font-mono text-sm font-bold text-rose-400 uppercase tracking-widest">Neural-Molecular Bridge // Layer 7</h2>
              <div className="text-[10px] font-mono text-rose-400/70">MultiverseManager gRPC Ingestion Stream (iOS/watchOS)</div>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-lg transition-colors">
            <X className="w-5 h-5 text-arkhe-muted" />
          </button>
        </div>

        <div className="flex-1 flex flex-col lg:flex-row p-6 gap-6 overflow-hidden">
          {/* Left: Live Biometric Data */}
          <div className="flex-1 flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div className="text-xs font-mono uppercase tracking-widest text-arkhe-muted">Consciousness Payload Stream</div>
              <button
                onClick={() => setIsConnected(!isConnected)}
                className={`flex items-center gap-2 text-[10px] font-mono px-2 py-1 rounded border transition-colors ${isConnected ? 'text-rose-400 bg-rose-400/10 border-rose-400/20' : 'text-arkhe-muted bg-black/40 border-white/5'}`}
              >
                <Activity className="w-3 h-3" />
                <span>{isConnected ? 'gRPC STREAM ACTIVE' : 'gRPC STREAM PAUSED'}</span>
              </button>
            </div>

            <div className="grid grid-cols-2 gap-4">
              {/* Heart Rate */}
              <div className="bg-[#111214] border border-[#1f2024] rounded-xl p-4 relative overflow-hidden">
                <div className="absolute -right-4 -top-4 opacity-5">
                  <HeartPulse className="w-24 h-24 text-rose-500" />
                </div>
                <div className="text-[10px] font-mono text-arkhe-muted uppercase mb-2">Heart Rate (Stochastic)</div>
                <div className="flex items-end gap-2">
                  <span className="text-4xl font-mono font-bold text-rose-400">
                    {latest ? latest.heartRate.toFixed(1) : '---'}
                  </span>
                  <span className="text-xs font-mono text-rose-400/50 mb-1">BPM</span>
                </div>
              </div>

              {/* HRV / Noise */}
              <div className="bg-[#111214] border border-[#1f2024] rounded-xl p-4 relative overflow-hidden">
                <div className="absolute -right-4 -top-4 opacity-5">
                  <Waves className="w-24 h-24 text-purple-500" />
                </div>
                <div className="text-[10px] font-mono text-arkhe-muted uppercase mb-2">HRV (Biological Noise)</div>
                <div className="flex items-end gap-2">
                  <span className="text-4xl font-mono font-bold text-purple-400">
                    {latest ? latest.hrvSdnn.toFixed(1) : '---'}
                  </span>
                  <span className="text-xs font-mono text-purple-400/50 mb-1">ms</span>
                </div>
              </div>

              {/* LF/HF Ratio */}
              <div className="bg-[#111214] border border-[#1f2024] rounded-xl p-4 relative overflow-hidden">
                <div className="text-[10px] font-mono text-arkhe-muted uppercase mb-2">Autonomic Balance (LF/HF)</div>
                <div className="flex items-end gap-2">
                  <span className={`text-3xl font-mono font-bold ${latest && latest.lfHfRatio > 1.5 ? 'text-orange-400' : 'text-emerald-400'}`}>
                    {latest ? latest.lfHfRatio.toFixed(2) : '---'}
                  </span>
                  <span className="text-xs font-mono text-arkhe-muted mb-1">Ratio</span>
                </div>
                <div className="text-[9px] font-mono text-arkhe-muted mt-2">
                  {latest && latest.lfHfRatio > 1.5 ? 'Sympathetic Dominance' : 'Parasympathetic Balance'}
                </div>
              </div>

              {/* IIT Phi */}
              <div className="bg-[#111214] border border-[#1f2024] rounded-xl p-4 relative overflow-hidden">
                <div className="text-[10px] font-mono text-arkhe-muted uppercase mb-2">Integrated Info (Φ)</div>
                <div className="flex items-end gap-2">
                  <span className="text-3xl font-mono font-bold text-cyan-400">
                    {latest ? latest.phiIit.toFixed(3) : '---'}
                  </span>
                  <span className="text-xs font-mono text-cyan-400/50 mb-1">IIT</span>
                </div>
                <div className="text-[9px] font-mono text-arkhe-muted mt-2">
                  Consciousness Integration Metric
                </div>
              </div>
            </div>

            {/* Coherence & Entropy */}
            <div className="bg-[#111214] border border-[#1f2024] rounded-xl p-4 flex-1 flex flex-col">
              <div className="flex items-center justify-between mb-4">
                <div className="text-[10px] font-mono text-arkhe-muted uppercase">Collective Coherence (λ₂)</div>
                <div className="text-xs font-mono text-emerald-400 font-bold flex items-center gap-2">
                  {latest && latest.coherenceIndex >= 1.618 && <span className="text-[9px] bg-purple-500/20 text-purple-400 px-1 rounded">TRANSCENDENT</span>}
                  {latest ? latest.coherenceIndex.toFixed(4) : '---'}
                </div>
              </div>

              {/* Coherence Bar */}
              <div className="w-full h-2 bg-black rounded-full overflow-hidden mb-6 relative">
                {/* Golden Ratio Marker */}
                <div className="absolute top-0 bottom-0 w-0.5 bg-yellow-400 z-10" style={{ left: '80.9%' }} title="Golden Ratio (φ)" />
                <motion.div
                  className="h-full bg-gradient-to-r from-rose-500 via-purple-500 to-emerald-500"
                  animate={{ width: latest ? `${(latest.coherenceIndex / 2.0) * 100}%` : '0%' }}
                  transition={{ type: 'spring', bounce: 0, duration: 1 }}
                />
              </div>

              <div className="text-[10px] font-mono text-arkhe-muted uppercase mb-2">Raw Entropy Seed (Hex)</div>
              <div className="bg-black/40 border border-white/5 rounded p-3 font-mono text-xs text-arkhe-muted break-all">
                {latest ? `0x${latest.rawEntropy}` : 'WAITING_FOR_STREAM...'}
              </div>
            </div>
          </div>

          {/* Right: gRPC Log */}
          <div className="w-full lg:w-96 flex flex-col gap-4">
            <div className="bg-[#111214] border border-[#1f2024] rounded-xl p-4 flex-1 flex flex-col overflow-hidden">
              <h3 className="text-xs font-mono uppercase tracking-widest text-rose-400 mb-4 border-b border-[#1f2024] pb-2 flex items-center gap-2">
                <Fingerprint className="w-4 h-4" />
                MultiverseManager Ingestion
              </h3>

              <div className="flex-1 overflow-y-auto space-y-2 pr-2">
                {payloads.map((p, i) => (
                  <motion.div
                    key={p.timestamp}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1 - (i * 0.1), x: 0 }}
                    className="bg-black/40 border border-white/5 p-2 rounded text-[9px] font-mono"
                  >
                    <div className="flex justify-between text-arkhe-muted mb-1">
                      <span>{new Date(p.timestamp).toISOString().split('T')[1].replace('Z', '')}</span>
                      <span className="text-rose-400/50">{p.nodeId}</span>
                    </div>
                    <div className="text-rose-400">
                      HR:{p.heartRate.toFixed(1)} | HRV:{p.hrvSdnn.toFixed(1)} | LF/HF:{p.lfHfRatio.toFixed(2)}
                    </div>
                    <div className="text-emerald-400 mt-1">
                      λ₂:{p.coherenceIndex.toFixed(3)} | Φ:{p.phiIit.toFixed(3)}
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
