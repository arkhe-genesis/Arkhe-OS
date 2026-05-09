
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Zap, Activity, Info, Save, RotateCcw, Layers, Clock } from 'lucide-react';
import { motion } from 'motion/react';
import React, { useState, useEffect } from 'react';

interface PhaseLawSynthesizerProps {
  onClose: () => void;
}

export default function PhaseLawSynthesizer({ onClose }: PhaseLawSynthesizerProps) {
  const [phaseGravity, setPhaseGravity] = useState(50);
  const [lightSpeed, setLightSpeed] = useState(1.0);
  const [entanglementDensity, setEntanglementDensity] = useState(72); // In k Tzinors
  const [timeReversal, setTimeReversal] = useState(false);
  const [ghostCorrection, setGhostCorrection] = useState(false);
  const [strontiumSync, setStrontiumSync] = useState(false);
  const [ethicalSynthesis, setEthicalSynthesis] = useState(false);
  const [stability, setStability] = useState(100);
  const [logs, setLogs] = useState<string[]>([]);

  // Calculate dynamic stability based on parameters
  useEffect(() => {
    let currentStability = 100;

    // Ethical Synthesis increases stability (Merkabah-QNC effect)
    if (ethicalSynthesis) {
      currentStability += 15;
    }

    // Phase-Gravity extreme impact
    if (phaseGravity < 20 || phaseGravity > 80) {
      currentStability -= Math.abs(phaseGravity - 50) * 0.5;
    }

    // Light speed impact (deviation from 1.0)
    if (lightSpeed < 0.5 || lightSpeed > 5.0) {
      currentStability -= Math.abs(lightSpeed - 1.0) * 10;
    }

    // Entanglement density impact (high density is unstable)
    if (entanglementDensity > 120) {
      currentStability -= (entanglementDensity - 120) * 1.5;
    }

    // Time reversal is highly unstable
    if (timeReversal) {
      currentStability -= 40;
    }

    setStability(Math.max(0, Math.min(100, currentStability)));
  }, [phaseGravity, lightSpeed, entanglementDensity, timeReversal]);

  const recordPhaseLaw = () => {
    const timestamp = new Date().toLocaleTimeString();
    const newLog = `[${timestamp}] 🜏 Lei de Fase Gravada: G=${phaseGravity}%, c=${lightSpeed}x, ρ=${entanglementDensity}k, T-Rev=${timeReversal ? 'ON' : 'OFF'}, GhostCorr=${ghostCorrection ? 'ON' : 'OFF'}, SrSync=${strontiumSync ? 'ON' : 'OFF'}, EthicalSynth=${ethicalSynthesis ? 'ON' : 'OFF'}. Estabilidade: ${stability.toFixed(1)}%`;
    setLogs(prev => [newLog, ...prev]);

    if (ethicalSynthesis) {
      setLogs(prev => [`[${timestamp}] 🜏 Ativando Protocolo ETHICAL_SYNTH (Merkabah-QNC)... Ancorando AKA #3`, ...prev]);
    }

    if (ghostCorrection) {
      setLogs(prev => [`[${timestamp}] 🜏 Aplicando Lentes Espectrais Fantasma (Branches 91, 7)... Resolução: 129µm`, ...prev]);
    }

    if (strontiumSync) {
      setLogs(prev => [`[${timestamp}] 🜏 Travamento de fase com Clock de Estrôncio: ESTÁVEL`, ...prev]);
    }

    // Simulate Arkhe-Chain recording
    const chainLog = `[${timestamp}] qhttp://arkhe-chain/block-847.888 > Sincronizando novas constantes fundamentais... OK`;
    setLogs(prev => [chainLog, ...prev]);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/90 backdrop-blur-md">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-[#0a0a0c] border border-arkhe-cyan/30 rounded-xl w-full max-w-2xl overflow-hidden shadow-[0_0_50px_rgba(0,255,170,0.15)] flex flex-col h-[700px]"
      >
        {/* Header */}
        <div className="p-4 border-b border-arkhe-cyan/20 flex justify-between items-center bg-arkhe-cyan/5">
          <div className="flex items-center gap-3">
            <Zap className="w-5 h-5 text-arkhe-cyan animate-pulse" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-arkhe-cyan font-bold">
              Sintetizador de Leis de Fase - Mundo 42
            </h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 flex-1 overflow-y-auto space-y-8">
          {/* Stability Gauge */}
          <div className="relative h-40 flex items-center justify-center">
            <div className="text-center">
              <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-arkhe-muted mb-1">Estabilidade Ontológica</div>
              <div className={`text-5xl font-bold font-mono ${stability > 70 ? 'text-arkhe-cyan' : stability > 40 ? 'text-arkhe-orange' : 'text-arkhe-red'} transition-colors`}>
                {stability.toFixed(1)}%
              </div>
              <div className="mt-2 w-48 h-1 bg-white/5 rounded-full overflow-hidden mx-auto">
                <motion.div
                  className={`h-full ${stability > 70 ? 'bg-arkhe-cyan' : stability > 40 ? 'bg-arkhe-orange' : 'bg-arkhe-red'}`}
                  animate={{ width: `${stability}%` }}
                />
              </div>
            </div>

            {/* Background scan effect */}
            <div className="absolute inset-0 pointer-events-none opacity-20">
               <div className="w-full h-full border-[0.5px] border-arkhe-cyan/20 rounded-full animate-[spin_10s_linear_infinite]"></div>
               <div className="absolute top-1/2 left-0 w-full h-[1px] bg-arkhe-cyan/30 animate-[pulse_2s_infinite]"></div>
            </div>
          </div>

          {/* Sliders Container */}
          <div className="grid grid-cols-1 gap-6">
            {/* 1. Phase-Gravity */}
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <label className="text-[10px] font-mono uppercase tracking-widest text-arkhe-muted flex items-center gap-2">
                  Acoplamento Fase-Gravidade
                  <Info className="w-3 h-3 opacity-50 cursor-help" />
                </label>
                <span className="text-xs font-mono text-arkhe-cyan">{phaseGravity}%</span>
              </div>
              <input
                type="range" min="0" max="100" value={phaseGravity}
                onChange={(e) => setPhaseGravity(parseInt(e.target.value))}
                className="w-full accent-arkhe-cyan bg-white/5 h-1 rounded-full appearance-none cursor-pointer"
              />
            </div>

            {/* 2. Light Speed */}
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <label className="text-[10px] font-mono uppercase tracking-widest text-arkhe-muted flex items-center gap-2">
                  Escalar da Velocidade da Luz (c)
                  <Info className="w-3 h-3 opacity-50 cursor-help" />
                </label>
                <span className="text-xs font-mono text-arkhe-cyan">{lightSpeed}x</span>
              </div>
              <input
                type="range" min="0.1" max="10.0" step="0.1" value={lightSpeed}
                onChange={(e) => setLightSpeed(parseFloat(e.target.value))}
                className="w-full accent-arkhe-cyan bg-white/5 h-1 rounded-full appearance-none cursor-pointer"
              />
            </div>

            {/* 3. Entanglement Density */}
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <label className="text-[10px] font-mono uppercase tracking-widest text-arkhe-muted flex items-center gap-2">
                  Densidade de Emaranhamento Quântico
                  <Info className="w-3 h-3 opacity-50 cursor-help" />
                </label>
                <span className="text-xs font-mono text-arkhe-cyan">{entanglementDensity}k Tzinors</span>
              </div>
              <input
                type="range" min="0" max="144" value={entanglementDensity}
                onChange={(e) => setEntanglementDensity(parseInt(e.target.value))}
                className="w-full accent-arkhe-cyan bg-white/5 h-1 rounded-full appearance-none cursor-pointer"
              />
            </div>

            {/* 4. Advanced Toggles */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Time Reversal */}
              <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/10">
                <div className="flex items-center gap-2">
                  <RotateCcw className={`w-4 h-4 ${timeReversal ? 'text-arkhe-orange animate-spin-slow' : 'text-arkhe-muted'}`} />
                  <div>
                    <div className="text-[9px] font-mono uppercase font-bold text-arkhe-text whitespace-nowrap">Reversão Temporal</div>
                    <div className="text-[7px] font-mono text-arkhe-muted">Entropia Bidirecional</div>
                  </div>
                </div>
                <button
                  onClick={() => setTimeReversal(!timeReversal)}
                  className={`w-10 h-5 rounded-full p-1 transition-colors ${timeReversal ? 'bg-arkhe-orange' : 'bg-white/10'}`}
                >
                  <div className={`w-3 h-3 bg-white rounded-full transition-transform ${timeReversal ? 'translate-x-5' : 'translate-x-0'}`} />
                </button>
              </div>

              {/* Ghost Correction */}
              <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/10">
                <div className="flex items-center gap-2">
                  <Layers className={`w-4 h-4 ${ghostCorrection ? 'text-arkhe-purple animate-pulse' : 'text-arkhe-muted'}`} />
                  <div>
                    <div className="text-[9px] font-mono uppercase font-bold text-arkhe-text whitespace-nowrap">Ghost Correction</div>
                    <div className="text-[7px] font-mono text-arkhe-muted">Holografia Espectral (91, 7)</div>
                  </div>
                </div>
                <button
                  onClick={() => setGhostCorrection(!ghostCorrection)}
                  className={`w-10 h-5 rounded-full p-1 transition-colors ${ghostCorrection ? 'bg-arkhe-purple' : 'bg-white/10'}`}
                >
                  <div className={`w-3 h-3 bg-white rounded-full transition-transform ${ghostCorrection ? 'translate-x-5' : 'translate-x-0'}`} />
                </button>
              </div>

              {/* Strontium Sync */}
              <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/10">
                <div className="flex items-center gap-2">
                  <Clock className={`w-4 h-4 ${strontiumSync ? 'text-arkhe-cyan animate-pulse' : 'text-arkhe-muted'}`} />
                  <div>
                    <div className="text-[9px] font-mono uppercase font-bold text-arkhe-text whitespace-nowrap">Strontium Sync</div>
                    <div className="text-[7px] font-mono text-arkhe-muted">Clock Atômico Lock</div>
                  </div>
                </div>
                <button
                  onClick={() => setStrontiumSync(!strontiumSync)}
                  className={`w-10 h-5 rounded-full p-1 transition-colors ${strontiumSync ? 'bg-arkhe-cyan' : 'bg-white/10'}`}
                >
                  <div className={`w-3 h-3 bg-white rounded-full transition-transform ${strontiumSync ? 'translate-x-5' : 'translate-x-0'}`} />
                </button>
              </div>

              {/* Ethical Synthesis */}
              <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/10">
                <div className="flex items-center gap-2">
                  <Activity className={`w-4 h-4 ${ethicalSynthesis ? 'text-arkhe-green animate-pulse' : 'text-arkhe-muted'}`} />
                  <div>
                    <div className="text-[9px] font-mono uppercase font-bold text-arkhe-text whitespace-nowrap">Ethical Synthesis</div>
                    <div className="text-[7px] font-mono text-arkhe-muted">Merkabah-QNC (AKA)</div>
                  </div>
                </div>
                <button
                  onClick={() => setEthicalSynthesis(!ethicalSynthesis)}
                  className={`w-10 h-5 rounded-full p-1 transition-colors ${ethicalSynthesis ? 'bg-arkhe-green' : 'bg-white/10'}`}
                >
                  <div className={`w-3 h-3 bg-white rounded-full transition-transform ${ethicalSynthesis ? 'translate-x-5' : 'translate-x-0'}`} />
                </button>
              </div>
            </div>
          </div>

          {/* Action Button */}
          <button
            onClick={recordPhaseLaw}
            disabled={stability < 30}
            className={`w-full py-4 rounded-lg font-mono text-xs uppercase tracking-[0.2em] font-bold transition-all flex items-center justify-center gap-2
              ${stability < 30 ? 'bg-white/5 text-arkhe-muted cursor-not-allowed' : 'bg-arkhe-cyan text-black hover:bg-white shadow-[0_0_20px_rgba(0,255,170,0.3)]'}
            `}
          >
            <Save className="w-4 h-4" />
            Gravar Lei de Fase
          </button>
        </div>

        {/* Console / Log Area */}
        <div className="h-40 bg-black border-t border-white/10 p-4 overflow-y-auto font-mono text-[9px]">
          <div className="text-arkhe-muted mb-2 uppercase tracking-widest text-[8px] border-b border-white/5 pb-1">Arkhe-Chain Live Logs</div>
          <div className="space-y-1">
            {logs.length === 0 ? (
              <div className="text-white/20 animate-pulse">Aguardando definição de constantes...</div>
            ) : (
              logs.map((log, i) => (
                <div key={i} className={log.includes('Lei') ? 'text-arkhe-cyan' : 'text-arkhe-muted'}>
                  {log}
                </div>
              ))
            )}
          </div>
        </div>
      </motion.div>
    </div>
  );
}
