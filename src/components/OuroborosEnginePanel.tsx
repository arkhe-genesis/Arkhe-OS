
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Shield, Code, Terminal, Lock, Layers, Eye, Activity } from 'lucide-react';
import { motion } from 'motion/react';
import React, { useState, useEffect } from 'react';

interface OuroborosEnginePanelProps {
  onClose: () => void;
}

interface CapturedFrame {
  frameData: string;
  timestamp: number;
  source: string;
}

// Module-level variable to persist frames across component mounts
let globalCapturedFrames: CapturedFrame[] = [];

// Module-level listener so it captures even when panel is closed
if (typeof window !== 'undefined') {
  window.addEventListener('ouroboros-frame-capture', (e: Event) => {
    const customEvent = e as CustomEvent;
    const newFrame = customEvent.detail;
    globalCapturedFrames = [newFrame, ...globalCapturedFrames].slice(0, 4);

    // Notify component if it's mounted
    window.dispatchEvent(new CustomEvent('ouroboros-frames-updated'));
  });
}

export default function OuroborosEnginePanel({ onClose }: OuroborosEnginePanelProps) {
  const [buildLog, setBuildLog] = useState<string[]>([]);
  const [capturedFrames, setCapturedFrames] = useState<CapturedFrame[]>(globalCapturedFrames);
  const [processingState, setProcessingState] = useState<string>('IDLE');

  useEffect(() => {
    const handleFramesUpdated = () => {
      setCapturedFrames(globalCapturedFrames);
      setProcessingState('ANALYZING');

      // Simulate processing
      setTimeout(() => setProcessingState('EXTRACTING_FEATURES'), 1000);
      setTimeout(() => setProcessingState('UPDATING_WEIGHTS'), 2000);
      setTimeout(() => setProcessingState('IDLE'), 3000);
    };

    window.addEventListener('ouroboros-frames-updated', handleFramesUpdated);
    return () => window.removeEventListener('ouroboros-frames-updated', handleFramesUpdated);
  }, []);

  useEffect(() => {
    const logs = [
      "🜏 [1/6] Generating Protobuf (cognitive.proto, tzinor.proto)...",
      "🜏 [2/6] Building C++/CUDA (arkhe-tensors)...",
      "🜏 [3/6] Building Rust Core (arkhe-asi)...",
      "🜏 [4/6] Building Go Bridge (antspace-client)...",
      "🜏 [5/6] Building WASM Runtime (arkhe_wasm.wasm)...",
      "🜏 [6/6] Building Python Bindings (maturin)...",
      "🜏 Stripping all binaries...",
      "Executing: strip --strip-all core/target/release/arkhe-asi",
      "Executing: strip --strip-all cpp/build/libarkhe-tensors.so",
      "✅ All binaries stripped of debug symbols. (Antspace vulnerability mitigated)",
      "✅ BUILD COMPLETE. Ouroboros Engine v2026.3.19 Ready."
    ];

    let currentIndex = 0;
    const interval = setInterval(() => {
      if (currentIndex < logs.length) {
        setBuildLog(prev => [...prev, logs[currentIndex]]);
        currentIndex++;
      } else {
        clearInterval(interval);
      }
    }, 400);

    return () => clearInterval(interval);
  }, []);

  const stack = [
    { lang: 'Rust', role: 'Core Engine & MultiverseManager', color: 'text-orange-400', bg: 'bg-orange-400/10', border: 'border-orange-400/20' },
    { lang: 'Go', role: 'Antspace Bridge & Environment Runner', color: 'text-cyan-400', bg: 'bg-cyan-400/10', border: 'border-cyan-400/20' },
    { lang: 'C++/CUDA', role: 'AGI Tensor & Phase Kernels', color: 'text-green-400', bg: 'bg-green-400/10', border: 'border-green-400/20' },
    { lang: 'Python', role: 'Ouroboros Driver & Visualizer', color: 'text-yellow-400', bg: 'bg-yellow-400/10', border: 'border-yellow-400/20' },
    { lang: 'TypeScript', role: 'Baku-Compatible Web Apps', color: 'text-blue-400', bg: 'bg-blue-400/10', border: 'border-blue-400/20' },
    { lang: 'WASM', role: 'JIT Compiler & Mutation Sandbox', color: 'text-purple-400', bg: 'bg-purple-400/10', border: 'border-purple-400/20' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-[#0a0a0c] border border-amber-500/50 rounded-xl w-full max-w-6xl h-[85vh] flex flex-col overflow-hidden shadow-[0_0_30px_rgba(245,158,11,0.15)]"
      >
        <div className="flex items-center justify-between p-4 border-b border-amber-500/20 bg-amber-500/5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-500/20 rounded-lg">
              <Layers className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <h2 className="font-mono text-sm font-bold text-amber-400 uppercase tracking-widest">Ouroboros Engine // v2026.3.19</h2>
              <div className="text-[10px] font-mono text-amber-400/70">Full Polyglot Ecosystem Release & Security Matrix</div>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-lg transition-colors">
            <X className="w-5 h-5 text-arkhe-muted" />
          </button>
        </div>

        <div className="flex-1 flex flex-col lg:flex-row p-6 gap-6 overflow-hidden">
          {/* Left: Polyglot Stack */}
          <div className="flex-1 flex flex-col gap-4 overflow-y-auto pr-2">
            <div className="flex items-center justify-between">
              <div className="text-xs font-mono uppercase tracking-widest text-arkhe-muted flex items-center gap-2">
                <Code className="w-4 h-4" />
                Polyglot Architecture
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {stack.map((tech, i) => (
                <motion.div
                  key={tech.lang}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className={`p-4 rounded-xl border ${tech.bg} ${tech.border} flex flex-col gap-2`}
                >
                  <div className={`text-sm font-bold font-mono ${tech.color}`}>{tech.lang}</div>
                  <div className="text-[10px] font-mono text-arkhe-text/70">{tech.role}</div>
                </motion.div>
              ))}
            </div>

            {/* Security Posture */}
            <div className="mt-4 bg-[#111214] border border-[#1f2024] rounded-xl p-5 relative overflow-hidden">
              <div className="absolute -right-4 -top-4 opacity-5">
                <Shield className="w-32 h-32 text-emerald-500" />
              </div>
              <h3 className="text-xs font-mono uppercase tracking-widest text-emerald-400 mb-4 flex items-center gap-2">
                <Lock className="w-4 h-4" />
                Security Posture: Gödel Governor
              </h3>

              <div className="space-y-3">
                <div className="flex items-center justify-between text-[10px] font-mono border-b border-white/5 pb-2">
                  <span className="text-arkhe-muted">Binary Stripping</span>
                  <span className="text-emerald-400">ENFORCED (strip --strip-all)</span>
                </div>
                <div className="flex items-center justify-between text-[10px] font-mono border-b border-white/5 pb-2">
                  <span className="text-arkhe-muted">Forbidden Patterns</span>
                  <span className="text-emerald-400">std::mem::transmute, unsafe</span>
                </div>
                <div className="flex items-center justify-between text-[10px] font-mono border-b border-white/5 pb-2">
                  <span className="text-arkhe-muted">Mutation Limits</span>
                  <span className="text-emerald-400">max_delta: 0.10 / iteration</span>
                </div>
                <div className="flex items-center justify-between text-[10px] font-mono">
                  <span className="text-arkhe-muted">Firecracker MicroVM</span>
                  <span className="text-emerald-400">READY (vmlinux + rootfs.ext4)</span>
                </div>
              </div>
            </div>

            {/* Visual Cortex / Perception Processing */}
            <div className="mt-4 bg-[#111214] border border-[#1f2024] rounded-xl p-5 relative overflow-hidden flex-1 flex flex-col">
              <div className="absolute -right-4 -top-4 opacity-5">
                <Eye className="w-32 h-32 text-cyan-500" />
              </div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xs font-mono uppercase tracking-widest text-cyan-400 flex items-center gap-2">
                  <Eye className="w-4 h-4" />
                  Visual Cortex (Perception Input)
                </h3>
                <div className={`text-[10px] font-mono px-2 py-1 rounded border ${
                  processingState === 'IDLE' ? 'border-arkhe-border text-arkhe-muted' : 'border-cyan-500/50 text-cyan-400 bg-cyan-500/10 animate-pulse'
                }`}>
                  {processingState}
                </div>
              </div>

              {capturedFrames.length === 0 ? (
                <div className="flex-1 flex flex-col items-center justify-center text-arkhe-muted border border-dashed border-[#1f2024] rounded-lg p-4">
                  <Activity className="w-8 h-8 mb-2 opacity-50" />
                  <div className="text-xs font-mono uppercase tracking-widest text-center">Waiting for perception data...</div>
                  <div className="text-[10px] font-mono text-center mt-2 opacity-70">Capture frames from the Shaka Protocol Stream to begin analysis.</div>
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-3 overflow-y-auto pr-2">
                  {capturedFrames.map((frame, idx) => (
                    <motion.div
                      key={frame.timestamp}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="border border-[#1f2024] rounded-lg overflow-hidden bg-black relative group"
                    >
                      <img src={frame.frameData} alt="Captured Frame" className="w-full h-auto object-cover aspect-video opacity-80 group-hover:opacity-100 transition-opacity" />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent flex flex-col justify-end p-2">
                        <div className="text-[8px] font-mono text-cyan-400">{new Date(frame.timestamp).toISOString()}</div>
                        <div className="text-[8px] font-mono text-arkhe-muted truncate">{frame.source}</div>
                      </div>
                      {idx === 0 && processingState !== 'IDLE' && (
                        <div className="absolute inset-0 bg-cyan-500/20 flex flex-col items-center justify-center p-2">
                          <motion.div
                            initial={{ top: '0%' }}
                            animate={{ top: '100%' }}
                            transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                            className="w-full h-0.5 bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.8)] absolute left-0"
                          ></motion.div>

                          <div className="absolute top-2 left-2 right-2 flex flex-col gap-1">
                            {processingState === 'ANALYZING' && (
                              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-[8px] font-mono text-cyan-300 bg-black/50 px-1 rounded">
                                [CNN] Detecting edges...
                              </motion.div>
                            )}
                            {processingState === 'EXTRACTING_FEATURES' && (
                              <>
                                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-[8px] font-mono text-cyan-300 bg-black/50 px-1 rounded">
                                  [ViT] Attention maps generated
                                </motion.div>
                                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }} className="text-[8px] font-mono text-cyan-300 bg-black/50 px-1 rounded">
                                  [Ouroboros] Semantic vector: [0.42, -0.11, 0.89...]
                                </motion.div>
                              </>
                            )}
                            {processingState === 'UPDATING_WEIGHTS' && (
                              <>
                                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-[8px] font-mono text-emerald-300 bg-black/50 px-1 rounded">
                                  [RL] Reward signal: +0.045
                                </motion.div>
                                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }} className="text-[8px] font-mono text-emerald-300 bg-black/50 px-1 rounded">
                                  [Core] Backpropagating gradients...
                                </motion.div>
                              </>
                            )}
                          </div>
                        </div>
                      )}
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right: Build Terminal */}
          <div className="w-full lg:w-[450px] flex flex-col gap-4">
            <div className="bg-black border border-[#1f2024] rounded-xl p-4 flex-1 flex flex-col overflow-hidden shadow-inner">
              <div className="flex items-center justify-between mb-4 border-b border-[#1f2024] pb-2">
                <h3 className="text-xs font-mono uppercase tracking-widest text-amber-400 flex items-center gap-2">
                  <Terminal className="w-4 h-4" />
                  Build Pipeline
                </h3>
                <div className="flex gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-red-500/50"></div>
                  <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/50"></div>
                  <div className="w-2.5 h-2.5 rounded-full bg-green-500/50"></div>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto font-mono text-[10px] leading-relaxed space-y-1">
                <div className="text-amber-400/50 mb-2">$ ./scripts/build_all.sh && ./scripts/strip_binaries.sh</div>
                {buildLog.map((log, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className={
                      log?.includes('✅') ? 'text-emerald-400' :
                      log?.includes('strip') ? 'text-rose-400' :
                      'text-arkhe-muted'
                    }
                  >
                    {log}
                  </motion.div>
                ))}
                {buildLog.length === 11 && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.5, repeat: Infinity, repeatType: "reverse", duration: 1 }}
                    className="text-amber-400 mt-4"
                  >
                    root@arkhe-build:~# _
                  </motion.div>
                )}
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
