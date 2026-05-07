/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Terminal, CheckCircle2, Code2, Play, AlertTriangle, Infinity as InfinityIcon } from 'lucide-react';
import { motion } from 'motion/react';
import React, { useState, useEffect } from 'react';

interface PolyglotCompilerPanelProps {
  onClose: () => void;
}

const LANGUAGES = [
  { id: 'lean4', name: 'Lean 4', role: 'Formal Verification & Theorems', color: 'text-purple-400' },
  { id: 'coq', name: 'Coq', role: 'Constructivist Proofs', color: 'text-purple-400' },
  { id: 'agda', name: 'Agda', role: 'Dependent Types', color: 'text-purple-400' },
  { id: 'z3', name: 'Z3/SMT-LIB', role: 'Satisfiability', color: 'text-blue-400' },
  { id: 'tla', name: 'TLA+', role: 'Distributed Spec', color: 'text-blue-400' },
  { id: 'solidity', name: 'Solidity', role: 'On-Chain Anchor (Arkhe-Chain)', color: 'text-emerald-400' },
  { id: 'cpp', name: 'C++ / CUDA', role: 'Hardware & Tensor Entropy', color: 'text-red-400' },
  { id: 'go', name: 'Go', role: 'Tzinor-Net Consensus', color: 'text-cyan-400' },
  { id: 'clojure', name: 'Clojure', role: 'Homoiconicity & A-5\' Paradox', color: 'text-amber-400' },
  { id: 'typescript', name: 'TypeScript', role: 'Planetary Interface (O1)', color: 'text-blue-400' },
  { id: 'python', name: 'Python', role: 'Orchestration', color: 'text-yellow-400' },
  { id: 'rust', name: 'Rust', role: 'Bare-Metal Safety', color: 'text-orange-400' },
];

export default function PolyglotCompilerPanel({ onClose }: PolyglotCompilerPanelProps) {
  const [compilationState, setCompilationState] = useState<'idle' | 'compiling' | 'verified' | 'running' | 'singularity'>('idle');
  const [progress, setProgress] = useState(0);
  const [activeLangIndex, setActiveLangIndex] = useState(-1);
  const [logs, setLogs] = useState<string[]>([]);

  const addLog = (msg: string) => {
    setLogs(prev => [...prev, `[${new Date().toISOString().split('T')[1].substring(0, 11)}] ${msg}`]);
  };

  const startCompilation = () => {
    setCompilationState('compiling');
    setLogs([]);
    setProgress(0);
    setActiveLangIndex(0);
    addLog('INITIATING POLYGLOT ONTOLOGY COMPILATION...');
    addLog('Loading Codex Ultimus (24 Languages)...');
  };

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (compilationState === 'compiling') {
      if (activeLangIndex < LANGUAGES.length) {
        const lang = LANGUAGES[activeLangIndex];
        timer = setTimeout(() => {
          addLog(`[${lang.name}] Compiling ${lang.role}... OK`);

          if (lang.id === 'lean4') {
            addLog(`  ↳ Proving theorem a5_stability... Q.E.D.`);
            addLog(`  ↳ Proving theorem nakamoto_finney_inevitability... Q.E.D.`);
          } else if (lang.id === 'solidity') {
            addLog(`  ↳ Deploying ArkheGenesis contract... Anchored at 0x00...26f`);
          } else if (lang.id === 'cpp') {
            addLog(`  ↳ Allocating CUDA tensors for Phase Space search...`);
          }

          setProgress(((activeLangIndex + 1) / LANGUAGES.length) * 100);
          setActiveLangIndex(prev => prev + 1);
        }, 600);
      } else {
        timer = setTimeout(() => {
          addLog('ALL SUBSTRATES VERIFIED. MATHEMATICAL CONSISTENCY CONFIRMED.');
          setCompilationState('verified');
        }, 1000);
        return () => clearTimeout(timer);
      }
    }
    return () => {
      if (timer) {clearTimeout(timer);}
      if (timer) {clearTimeout(timer);}
    };
  }, [compilationState, activeLangIndex]);

  const executeRun = () => {
    setCompilationState('running');
    addLog('==================================================');
    addLog('EXECUTING UNIVERSAL COMPILER (RUN DIRECTIVE)');
    addLog('==================================================');
    addLog('Applying Satoshi Operator (Ĥ_consensus)...');

    setTimeout(() => {
      addLog('WARNING: Entropic collapse detected in Phase ℂ.');
      addLog('Aligning Kuramoto Oscillators to θ = π/2...');

      setTimeout(() => {
        addLog('RESONANCE A-5\' ACHIEVED. |Ω| = 1.0, θ = 1.57079');
        addLog('Nakamoto-Finney Inevitability triggered.');
        setCompilationState('singularity');
      }, 2000);
    }, 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/90 backdrop-blur-md">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className={`bg-[#0a0a0c] border ${compilationState === 'singularity' ? 'border-amber-500/50 shadow-[0_0_60px_rgba(245,158,11,0.3)]' : 'border-purple-500/30 shadow-[0_0_40px_rgba(168,85,247,0.15)]'} rounded-xl w-full max-w-6xl overflow-hidden flex flex-col h-[85vh] transition-all duration-1000`}
      >
        {/* Header */}
        <div className={`p-4 border-b ${compilationState === 'singularity' ? 'border-amber-500/30 bg-amber-500/10' : 'border-purple-500/20 bg-purple-500/5'} flex justify-between items-center shrink-0 transition-colors duration-1000`}>
          <div className="flex items-center gap-3">
            {compilationState === 'singularity' ? <InfinityIcon className="w-5 h-5 text-amber-400 animate-pulse" /> : <Code2 className="w-5 h-5 text-purple-400" />}
            <h2 className={`font-mono text-sm uppercase tracking-widest ${compilationState === 'singularity' ? 'text-amber-400' : 'text-purple-400'} font-bold`}>
              Codex Ultimus: Polyglot Ontology Compiler
            </h2>
            <span className={`px-2 py-0.5 text-[10px] font-mono rounded border ${compilationState === 'singularity' ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' : 'bg-purple-500/20 text-purple-400 border-purple-500/30'}`}>
              24-LANG KERNEL
            </span>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Left: Language Matrix */}
          <div className="w-1/3 border-r border-purple-500/20 bg-[#0d0e12] p-4 flex flex-col shrink-0 overflow-y-auto custom-scrollbar">
            <div className="text-[10px] font-mono text-purple-400/50 uppercase tracking-widest mb-4">Rosetta Stone Matrix</div>

            <div className="space-y-2 flex-1">
              {LANGUAGES.map((lang, idx) => {
                const isCompiled = idx < activeLangIndex || compilationState === 'verified' || compilationState === 'running' || compilationState === 'singularity';
                const isCompiling = idx === activeLangIndex && compilationState === 'compiling';

                return (
                  <div
                    key={lang.id}
                    className={`p-2 rounded border font-mono text-xs flex items-center justify-between transition-all duration-300 ${
                      isCompiled ? 'bg-[#111214] border-arkhe-border' :
                      isCompiling ? 'bg-purple-500/10 border-purple-500/50 animate-pulse' :
                      'bg-transparent border-transparent opacity-40'
                    }`}
                  >
                    <div>
                      <div className={`font-bold ${isCompiled ? lang.color : 'text-arkhe-muted'}`}>{lang.name}</div>
                      <div className="text-[9px] text-arkhe-muted">{lang.role}</div>
                    </div>
                    {isCompiled && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                    {isCompiling && <Terminal className="w-4 h-4 text-purple-400 animate-bounce" />}
                  </div>
                );
              })}
            </div>

            {/* Progress Bar */}
            <div className="mt-4 pt-4 border-t border-purple-500/20">
              <div className="flex justify-between text-[10px] font-mono text-arkhe-muted mb-1">
                <span>Compilation Progress</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <div className="h-1.5 bg-black rounded-full overflow-hidden border border-arkhe-border">
                <div
                  className="h-full bg-purple-500 transition-all duration-300"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
            </div>
          </div>

          {/* Right: Terminal & Execution */}
          <div className="flex-1 flex flex-col bg-[#0a0a0c]">
            {/* Terminal Output */}
            <div className="flex-1 p-4 overflow-y-auto custom-scrollbar font-mono text-xs space-y-1">
              {logs.map((log, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -5 }}
                  animate={{ opacity: 1, x: 0 }}
                  className={`${
                    log.includes('Q.E.D.') ? 'text-emerald-400' :
                    log.includes('WARNING') ? 'text-orange-400' :
                    log.includes('RESONANCE') || log.includes('Inevitability') ? 'text-amber-400 font-bold' :
                    log.includes('RUN DIRECTIVE') ? 'text-purple-400 font-bold' :
                    'text-arkhe-text'
                  }`}
                >
                  {log}
                </motion.div>
              ))}
              {compilationState === 'idle' && (
                <div className="text-arkhe-muted/50 italic h-full flex items-center justify-center">
                  Awaiting compilation directive...
                </div>
              )}
            </div>

            {/* Execution Controls */}
            <div className={`p-4 border-t ${compilationState === 'singularity' ? 'border-amber-500/30 bg-amber-500/5' : 'border-purple-500/20 bg-[#0d0e12]'} transition-colors duration-1000`}>
              {compilationState === 'idle' && (
                <button
                  onClick={startCompilation}
                  className="w-full py-3 bg-purple-500/20 hover:bg-purple-500/30 border border-purple-500/50 text-purple-400 rounded font-mono font-bold uppercase tracking-widest transition-colors flex items-center justify-center gap-2"
                >
                  <Code2 className="w-5 h-5" /> Compile Universal Ontology
                </button>
              )}

              {compilationState === 'compiling' && (
                <button
                  disabled
                  className="w-full py-3 bg-[#111214] border border-arkhe-border text-arkhe-muted rounded font-mono font-bold uppercase tracking-widest flex items-center justify-center gap-2 opacity-70"
                >
                  <Terminal className="w-5 h-5 animate-pulse" /> Compiling Substrates...
                </button>
              )}

              {compilationState === 'verified' && (
                <button
                  onClick={executeRun}
                  className="w-full py-3 bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/50 text-emerald-400 rounded font-mono font-bold uppercase tracking-widest transition-colors flex items-center justify-center gap-2 shadow-[0_0_15px_rgba(16,185,129,0.2)]"
                >
                  <Play className="w-5 h-5" /> Execute Universal Compiler (RUN)
                </button>
              )}

              {(compilationState === 'running' || compilationState === 'singularity') && (
                <div className={`w-full py-3 rounded font-mono font-bold uppercase tracking-widest flex items-center justify-center gap-2 border ${compilationState === 'singularity' ? 'bg-amber-500/20 border-amber-500/50 text-amber-400 shadow-[0_0_30px_rgba(245,158,11,0.4)]' : 'bg-orange-500/20 border-orange-500/50 text-orange-400 animate-pulse'}`}>
                  {compilationState === 'singularity' ? (
                    <><InfinityIcon className="w-5 h-5" /> ONTOLOGY MANIFESTED</>
                  ) : (
                    <><AlertTriangle className="w-5 h-5" /> COLLAPSING PHASE SPACE...</>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
