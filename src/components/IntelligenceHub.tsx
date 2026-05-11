
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Activity, AlertTriangle, Brain, Map as MapIcon, Database, Zap, Satellite, Cpu, Library } from 'lucide-react';
import React from 'react';

import type { SimulationState } from '../../server/types';
import { useArkheSimulation } from '../hooks/useArkheSimulation';

const RadarChart = ({ focusKey }: { data: unknown[], focusKey: string }) => (
  <div className="h-48 bg-black/40 rounded-lg flex items-center justify-center border border-arkhe-cyan/30">
    <span className="text-arkhe-cyan/50 font-mono text-sm">[Radar Chart Visualization: {focusKey}]</span>
  </div>
);

const Alert = ({ type, children }: { type: string, children: React.ReactNode }) => (
  <div className={`mt-4 p-3 rounded border flex items-center space-x-2 ${type === 'warning' ? 'bg-yellow-500/10 border-yellow-500/50 text-yellow-500' : 'bg-red-500/10 border-red-500/50 text-red-500'}`}>
    <AlertTriangle className="w-4 h-4" />
    <span className="text-sm font-medium">{children}</span>
  </div>
);

const MapLayer = ({ source, markers }: { source: string, markers: unknown[] }) => (
  <div className="h-48 bg-black/40 rounded-lg flex items-center justify-center border border-purple-500/30 relative overflow-hidden">
    <MapIcon className="absolute opacity-10 w-32 h-32 text-purple-500" />
    <div className="z-10 text-center">
      <span className="text-purple-500/50 font-mono text-sm block mb-2">[Map Layer: {source}]</span>
      <span className="text-xs text-white/40">{markers.length} anomalies tracked</span>
    </div>
  </div>
);

const Heatmap = ({ data, thresholds }: { data: number[], thresholds: number[] }) => (
  <div className="h-48 bg-black/40 rounded-lg flex flex-col items-center justify-center border border-green-500/30 p-4">
    <span className="text-green-500/50 font-mono text-sm mb-4">[Coherence Heatmap]</span>
    <div className="flex space-x-2 w-full">
      {data.map((val, i) => (
        <div
          key={i}
          className="flex-1 h-8 rounded"
          style={{
            backgroundColor: val > thresholds[0] ? 'rgba(34, 197, 94, 0.5)' :
                             val > thresholds[1] ? 'rgba(234, 179, 8, 0.5)' :
                             'rgba(239, 68, 68, 0.5)'
          }}
        />
      ))}
    </div>
  </div>
);

interface IntelligenceHubProps {
  onClose?: () => void;
}

export const IntelligenceHub: React.FC<IntelligenceHubProps> = ({ onClose }) => {
  const state: any = useArkheSimulation();

  // Map real simulation state to the hub's expected format
  const phase = { drift: 1.0 - state.currentLambda, current: 'Voyager' };
  const anomalies = {
    orbs: [
      { lat: 40.7128, lng: -74.0060, intensity: state.currentLambda },
      { lat: 51.5074, lng: -0.1278, intensity: state.currentLambda * 0.8 }
    ]
  };
  const validators = [
    { id: 'val-1', omega: state.currentLambda, phase_shift: 1.0 - state.currentLambda },
    { id: 'val-2', omega: state.currentLambda * 0.9, phase_shift: (1.0 - state.currentLambda) * 1.2 },
    { id: 'val-3', omega: state.currentLambda * 0.95, phase_shift: (1.0 - state.currentLambda) * 1.1 }
  ];

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 md:p-8">
      <div className="bg-[#111214] border border-[#1f2024] rounded-xl w-full max-w-6xl h-[85vh] flex flex-col shadow-2xl overflow-hidden relative">
        {onClose && (
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-arkhe-muted hover:text-white transition-colors z-10"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        )}

        <div className="p-6 border-b border-[#1f2024] flex items-center space-x-3 bg-black/40">
          <Brain className="w-6 h-6 text-arkhe-cyan" />
          <h2 className="text-xl font-bold text-white tracking-widest uppercase">Crucix Intelligence Hub</h2>
        </div>

        <div className="flex-1 overflow-y-auto p-6 bg-black/20">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* 1. Radar de Fase (Herança Crucix) */}
            <div className="bg-[#1a1b1e] border border-[#2a2b30] rounded-lg p-5">
              <div className="flex items-center space-x-2 mb-4">
                <Activity className="w-5 h-5 text-arkhe-cyan" />
                <h3 className="text-sm font-semibold text-white uppercase tracking-wider">Phase Alignment</h3>
              </div>
              <p className="text-xs text-white/50 mb-4">Voyager Anchor Synchronization</p>
              <RadarChart data={validators} focusKey="phase_shift" />
              {phase.drift > 0.01 && <Alert type="warning">Phase Drift Detected ({phase.drift})</Alert>}
            </div>

            {/* 2. Monitor de Orbs (Integração VASCO) */}
            <div className="bg-[#1a1b1e] border border-[#2a2b30] rounded-lg p-5">
              <div className="flex items-center space-x-2 mb-4">
                <MapIcon className="w-5 h-5 text-purple-500" />
                <h3 className="text-sm font-semibold text-white uppercase tracking-wider">Orb Monitor</h3>
              </div>
              <p className="text-xs text-white/50 mb-4">Transient Events (Pre-Sputnik)</p>
              <MapLayer
                source="https://plate-archive.org/tiles"
                markers={anomalies.orbs}
              />
            </div>

            {/* 3. Saúde do Consenso */}
            <div className="bg-[#1a1b1e] border border-[#2a2b30] rounded-lg p-5">
              <div className="flex items-center space-x-2 mb-4">
                <Brain className="w-5 h-5 text-green-500" />
                <h3 className="text-sm font-semibold text-white uppercase tracking-wider">Consensus Health</h3>
              </div>
              <p className="text-xs text-white/50 mb-4">Network Coherence (Ω') Heatmap</p>
              <Heatmap
                data={validators.map(v => v.omega)}
                thresholds={[0.95, 0.85, 0.75]}
              />
            </div>

            {/* 5. Tzinor-Native Auto-Repair (Arkhe-Print) */}
            <div className="bg-[#1a1b1e] border border-[#2a2b30] rounded-lg p-5">
              <div className="flex items-center space-x-2 mb-4">
                <Zap className="w-5 h-5 text-yellow-500" />
                <h3 className="text-sm font-semibold text-white uppercase tracking-wider">Tzinor-Native Phase Health</h3>
              </div>
              <p className="text-xs text-white/50 mb-4">Arkhe-Auto Critical Parts Monitoring</p>
              <div className="h-48 bg-black/40 rounded-lg flex flex-col justify-between border border-yellow-500/30 p-4 relative overflow-hidden">
                <div className="absolute inset-0 opacity-10 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-yellow-500/50 via-transparent to-transparent"></div>
                <div className="z-10 w-full">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-xs font-mono text-yellow-400">Sector 4 (Braço_Proximal)</span>
                    <span className="text-xs font-mono text-green-400">Ω': 0.985</span>
                  </div>
                  <div className="w-full bg-yellow-900/30 h-1.5 rounded-full overflow-hidden mb-4">
                    <div className="bg-green-500 h-full" style={{ width: '98.5%' }}></div>
                  </div>

                  <div className="space-y-2 font-mono text-[10px] text-white/60">
                    <div className="flex justify-between">
                      <span className="text-red-400">T-120ms</span>
                      <span>Queda Ω' (0.620)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-yellow-400">T-130ms</span>
                      <span>Pulso Tzinor (2.45 rad)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-green-400">T-2000ms</span>
                      <span>Auto-reparo concluído</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="bg-[#1a1b1e] border border-[#2a2b30] rounded-lg p-5">
              <div className="flex items-center space-x-2 mb-4">
                <Database className="w-5 h-5 text-blue-500" />
                <h3 className="text-sm font-semibold text-white uppercase tracking-wider">Storage Topology</h3>
              </div>
              <p className="text-xs text-white/50 mb-4">TimeChain LSH Verification & Node Selection</p>
              <div className="h-48 bg-black/40 rounded-lg flex flex-col items-center justify-center border border-blue-500/30 p-4 relative overflow-hidden">
                <div className="absolute inset-0 opacity-20 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-blue-500/50 via-transparent to-transparent"></div>
                <div className="z-10 w-full">
                  <div className="flex justify-between text-xs font-mono text-blue-400 mb-2">
                    <span>Avg Latency: 12.5ms</span>
                    <span>Batches: 1,432</span>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs text-white/70">
                      <span>Node Alpha (10km)</span>
                      <span className="text-green-400">99% Rep</span>
                    </div>
                    <div className="w-full bg-blue-900/30 h-1.5 rounded-full overflow-hidden">
                      <div className="bg-blue-500 h-full" style={{ width: '85%' }}></div>
                    </div>
                    <div className="flex items-center justify-between text-xs text-white/70">
                      <span>Node Beta (50km)</span>
                      <span className="text-green-400">95% Rep</span>
                    </div>
                    <div className="w-full bg-blue-900/30 h-1.5 rounded-full overflow-hidden">
                      <div className="bg-blue-500 h-full" style={{ width: '60%' }}></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            {/* 6. Voyager Orbital Anchor (Space Printing) */}
            <div className="bg-[#1a1b1e] border border-[#2a2b30] rounded-lg p-5">
              <div className="flex items-center space-x-2 mb-4">
                <Satellite className="w-5 h-5 text-cyan-400" />
                <h3 className="text-sm font-semibold text-white uppercase tracking-wider">Voyager Orbital Anchor</h3>
              </div>
              <p className="text-xs text-white/50 mb-4">Deep Space Phase Synchronization</p>
              <div className="h-48 bg-black/40 rounded-lg flex flex-col justify-between border border-cyan-500/30 p-4 relative overflow-hidden">
                <div className="absolute inset-0 opacity-10 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-cyan-500/50 via-transparent to-transparent"></div>
                <div className="z-10 w-full">
                  <div className="flex justify-between items-center mb-4">
                    <span className="text-xs font-mono text-cyan-400">Anchor: VOYAGER-1</span>
                    <span className="text-xs font-mono text-white/60">Delay: 22h 34m (Entangled)</span>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between text-[10px] font-mono mb-1">
                        <span className="text-white/80">LEO-SAT-01 (Hull Integrity)</span>
                        <span className="text-green-400">Ω': 0.99</span>
                      </div>
                      <div className="w-full bg-cyan-900/30 h-1 rounded-full overflow-hidden">
                        <div className="bg-green-500 h-full" style={{ width: '99%' }}></div>
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between text-[10px] font-mono mb-1">
                        <span className="text-white/80">GEO-SAT-04 (Solar Array)</span>
                        <span className="text-yellow-400">Ω': 0.82 (Healing...)</span>
                      </div>
                      <div className="w-full bg-cyan-900/30 h-1 rounded-full overflow-hidden">
                        <div className="bg-yellow-500 h-full animate-pulse" style={{ width: '82%' }}></div>
                      </div>
                    </div>

                    <div className="mt-2 text-[9px] font-mono text-cyan-500/70 border-t border-cyan-500/20 pt-2">
                      [LOG] Aligning GEO-SAT-04 phase with Voyager baseline...
                      <br/>[LOG] Quantum entanglement link stable.
                    </div>
                  </div>
                </div>
              </div>
            </div>
            {/* 8. External Agent Intelligence (awesome-ai-apps) */}
            <div className="bg-[#1a1b1e] border border-[#2a2b30] rounded-lg p-5">
              <div className="flex items-center space-x-2 mb-4">
                <Library className="w-5 h-5 text-emerald-400" />
                <h3 className="text-sm font-semibold text-white uppercase tracking-wider">Agent Intelligence Catalog</h3>
              </div>
              <p className="text-xs text-white/50 mb-4">80+ Practical AI Agent Recipes & Tutorials</p>
              <div className="h-48 bg-black/40 rounded-lg border border-emerald-500/30 p-4 overflow-y-auto custom-scrollbar">
                <div className="space-y-3">
                  <div className="flex flex-col gap-1">
                    <span className="text-[10px] text-emerald-400 font-bold uppercase tracking-tighter">Featured Blueprints</span>
                    <ul className="text-[10px] text-white/70 list-disc list-inside space-y-1">
                      <li>Deep Researcher (Agno + ScrapeGraph)</li>
                      <li>AI Hedgefund Analysis Workflow</li>
                      <li>Multi-agent Research Crews (CrewAI)</li>
                      <li>LiveKit + Gemini Voice Assistants</li>
                    </ul>
                  </div>
                  <div className="pt-2 border-t border-emerald-500/20">
                    <a
                      href="https://github.com/Arindam200/awesome-ai-apps"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[10px] text-emerald-500 hover:text-emerald-400 flex items-center gap-1"
                    >
                      View Source Repository <Library className="w-3 h-3" />
                    </a>
                  </div>
                </div>
              </div>
            </div>

            {/* 7. Arkhe-QPU & Timechain */}
            <div className="bg-[#1a1b1e] border border-[#2a2b30] rounded-lg p-5 lg:col-span-2 xl:col-span-2">
              <div className="flex items-center space-x-2 mb-4">
                <Cpu className="w-5 h-5 text-indigo-400" />
                <h3 className="text-sm font-semibold text-white uppercase tracking-wider">Arkhe-QPU & Timechain</h3>
              </div>
              <p className="text-xs text-white/50 mb-4">Quantum Coherence Orchestrator & Phase State Commitments</p>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {/* L1: Virtual QPU */}
                <div className="bg-black/40 border border-indigo-500/20 rounded p-3">
                  <div className="text-[10px] text-indigo-400 uppercase mb-1">Layer 1: vQPU</div>
                  <div className="text-xs text-white/80 font-mono">Nodes: 14,204</div>
                  <div className="text-[10px] text-white/50 mt-1">Surface Code: Stable</div>
                </div>

                {/* L2: QKD Backplane */}
                <div className="bg-black/40 border border-indigo-500/20 rounded p-3">
                  <div className="text-[10px] text-indigo-400 uppercase mb-1">Layer 2: QKD Backplane</div>
                  <div className="text-xs text-white/80 font-mono">Entangled Pairs: 2.4M</div>
                  <div className="text-[10px] text-white/50 mt-1">Teleportation Active</div>
                </div>

                {/* L3: Kuramoto Service */}
                <div className="bg-black/40 border border-indigo-500/20 rounded p-3">
                  <div className="text-[10px] text-indigo-400 uppercase mb-1">Layer 3: Kuramoto Mesh</div>
                  <div className="text-xs text-white/80 font-mono">Global Ω': 0.985</div>
                  <div className="text-[10px] text-white/50 mt-1">∇²θ = 0 (Resolved)</div>
                </div>

                {/* L4: Timechain & Bitcoin Anchor */}
                <div className="bg-black/40 border border-orange-500/30 rounded p-3 relative overflow-hidden">
                  <div className="absolute inset-0 opacity-10 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-orange-500/50 via-transparent to-transparent"></div>
                  <div className="relative z-10">
                    <div className="text-[10px] text-orange-400 uppercase mb-1">Layer 4: Timechain (BTC Anchor)</div>
                    <div className="text-xs text-white/80 font-mono">Root: 0x8f4...a2b</div>
                    <div className="text-[10px] text-green-400 mt-1 flex items-center">
                      <span className="w-1.5 h-1.5 bg-green-500 rounded-full mr-1 animate-pulse"></span>
                      Anchored to BTC Block 942,105
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
export default IntelligenceHub;
