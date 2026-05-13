import React, { useState, useEffect } from 'react';
import { Activity, Beaker, Network, Dna, FileText } from 'lucide-react';
import { motion } from 'motion/react';

interface BioDashboardPanelProps {
  onClose?: () => void;
}

export default function BioDashboardPanel({ onClose }: BioDashboardPanelProps) {
  return (
    <div className="flex flex-col h-full bg-gray-900 text-cyan-400 p-4 rounded-xl border border-cyan-800 shadow-2xl relative overflow-hidden">
      <div className="flex justify-between items-center mb-4 border-b border-cyan-800 pb-2">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Dna className="text-cyan-400" />
          Biological Systems Dashboard (v6.0.1)
        </h2>
        {onClose && (
          <button onClick={onClose} className="hover:bg-cyan-900 p-1 rounded">
             <Activity className="w-5 h-5 text-cyan-400" />
          </button>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4 flex-grow overflow-y-auto pr-2">
        {/* Junk DNA vs Radiation Correlation Panel */}
        <div className="bg-gray-800 p-4 rounded-lg border border-cyan-900 flex flex-col">
          <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
             <Activity className="w-4 h-4" />
             Junk-DNA × Radiation Resilience
          </h3>
          <div className="flex-grow flex items-center justify-center bg-gray-900 rounded border border-gray-700 relative overflow-hidden">
             <div className="text-sm text-gray-500 absolute top-2 left-2">Extremophiles Dataset (n=53)</div>
             {/* Simulated Scatter Plot Area */}
             <div className="w-full h-full relative p-4">
                 <div className="absolute left-4 bottom-4 top-4 border-l border-cyan-700"></div>
                 <div className="absolute left-4 bottom-4 right-4 border-b border-cyan-700"></div>
                 {Array.from({ length: 50 }).map((_, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, scale: 0 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: i * 0.05 }}
                      className="absolute w-2 h-2 rounded-full bg-cyan-400"
                      style={{
                        left: `calc(1rem + ${10 + Math.random() * 80}%)`,
                        bottom: `calc(1rem + ${10 + Math.random() * 80}%)`,
                        opacity: 0.6 + Math.random() * 0.4
                      }}
                    />
                 ))}
                 <div className="absolute bottom-1 w-full text-center text-xs text-cyan-600">Junk DNA %</div>
                 <div className="absolute left-[-1.5rem] top-1/2 -rotate-90 text-xs text-cyan-600">Rad Resistance (kGy)</div>
             </div>
          </div>
        </div>

        {/* Chaperone Folding Energy Panel */}
        <div className="bg-gray-800 p-4 rounded-lg border border-cyan-900 flex flex-col">
          <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
             <Network className="w-4 h-4" />
             Chaperone-Assisted Folding (Φ_C)
          </h3>
          <div className="flex-grow flex flex-col gap-2">
              <div className="flex-grow bg-gray-900 rounded border border-gray-700 relative p-2">
                 <div className="text-xs text-gray-400 mb-1">Energy Landscape (Hsp70 vs Unassisted)</div>
                 <svg viewBox="0 0 100 50" className="w-full h-24 stroke-cyan-500 fill-none" preserveAspectRatio="none">
                    <motion.path
                       initial={{ pathLength: 0 }}
                       animate={{ pathLength: 1 }}
                       transition={{ duration: 2, ease: "linear" }}
                       d="M0,45 Q20,10 40,30 T80,45"
                       className="stroke-red-500 opacity-50 stroke-[1.5]"
                    />
                    <motion.path
                       initial={{ pathLength: 0 }}
                       animate={{ pathLength: 1 }}
                       transition={{ duration: 2, ease: "linear", delay: 0.5 }}
                       d="M0,45 Q25,-10 50,20 T100,45"
                       className="stroke-cyan-400 stroke-2"
                    />
                 </svg>
                 <div className="flex justify-between text-[10px] mt-1 text-gray-500">
                    <span>Unfolded</span>
                    <span className="text-cyan-400">Native State</span>
                 </div>
              </div>
              <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="bg-gray-900 p-2 rounded">
                      <div className="text-gray-500 text-xs">GroEL Coherence</div>
                      <div className="text-cyan-300 font-mono">0.984 Φ_C</div>
                  </div>
                  <div className="bg-gray-900 p-2 rounded">
                      <div className="text-gray-500 text-xs">Folding Time</div>
                      <div className="text-cyan-300 font-mono">14.2 µs</div>
                  </div>
              </div>
          </div>
        </div>

        {/* GECC Genomic Repair Protocol */}
        <div className="bg-gray-800 p-4 rounded-lg border border-cyan-900 flex flex-col col-span-2">
          <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
             <Beaker className="w-4 h-4" />
             GECC Reed-Solomon Simulation Live
          </h3>
           <div className="bg-black rounded border border-cyan-900 p-3 font-mono text-xs overflow-hidden h-32 flex flex-col">
              <div className="text-gray-500 mb-1 border-b border-gray-800 pb-1 flex justify-between">
                 <span>[BERLEKAMP-MASSEY + FORNEY DECODING]</span>
                 <span className="text-green-400">ONLINE</span>
              </div>
              <motion.div
                 animate={{ y: [0, -200] }}
                 transition={{ repeat: Infinity, duration: 10, ease: "linear" }}
                 className="space-y-1 text-cyan-300 opacity-80"
              >
                  {Array.from({ length: 20 }).map((_, i) => (
                      <div key={i} className="flex gap-4">
                         <span className="text-gray-600">{1000 + i * 7}</span>
                         <span>RECV: {Math.random().toString(16).substr(2, 16).toUpperCase()}</span>
                         <span className={Math.random() > 0.8 ? "text-red-400" : "text-gray-500"}>ERR_DETECT</span>
                         <span className="text-green-500">CORRECTED</span>
                      </div>
                  ))}
              </motion.div>
           </div>
        </div>

      </div>

      <div className="mt-4 pt-3 border-t border-cyan-900 flex justify-between items-center text-xs">
          <div className="flex items-center gap-2 text-gray-400">
             <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
             ORCID Auth Active | Syncing to TemporalChain
          </div>
          <button className="flex items-center gap-1 bg-cyan-900 hover:bg-cyan-800 text-cyan-100 px-3 py-1 rounded transition-colors">
              <FileText className="w-3 h-3" />
              Export to LaTeX (Paper 91)
          </button>
      </div>
    </div>
  );
}
