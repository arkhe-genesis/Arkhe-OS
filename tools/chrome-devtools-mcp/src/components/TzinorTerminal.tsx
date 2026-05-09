
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Terminal } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import React, { useEffect, useState } from 'react';

import type { TzinorMemoryState } from '../types/tzinor';

interface TzinorTerminalProps {
  tzinor: TzinorMemoryState;
  threatLevel: 'normal' | 'warning' | 'critical';
}

const CHAR_PALETTE = [' ', '.', ':', '-', '=', '+', '*', '#', '%', '@', 'Ψ', 'Φ', 'λ', '🜏'];
const GRID_ROWS = 12;
const GRID_COLS = 48;

export default function TzinorTerminal({ tzinor, threatLevel }: TzinorTerminalProps) {
  const [grid, setGrid] = useState<Array<Array<{ char: string; color: string }>>>([]);
  const [lastUpdate, setLastUpdate] = useState(Date.now());

  useEffect(() => {
    setLastUpdate(Date.now());
    // Generate the ASCII grid based on Tzinor state
    const newGrid: Array<Array<{ char: string; color: string }>> = Array(GRID_ROWS).fill(null).map(() =>
      Array(GRID_COLS).fill({ char: ' ', color: 'text-arkhe-muted' })
    );

    // Render Background (Vacuum Fluctuations)
    const timeOffset = Date.now() / 1000;
    for (let r = 0; r < GRID_ROWS; r++) {
      for (let c = 0; c < GRID_COLS; c++) {
        // Simple noise function for background
        const noise = Math.sin(r * 0.5 + timeOffset) * Math.cos(c * 0.3 + timeOffset);
        if (noise > 0.8) {
          newGrid[r][c] = { char: '.', color: 'text-[#1f2024]' };
        } else if (noise < -0.8) {
          newGrid[r][c] = { char: ':', color: 'text-[#1f2024]' };
        }
      }
    }

    // Render gMemory (Consolidated Memory - The Genesis Engram)
    // We'll place it at the center as a stable core
    const coreR = Math.floor(GRID_ROWS / 2);
    const coreC = Math.floor(GRID_COLS / 2);

    tzinor.gMemory.forEach((engram, _idx) => {
      // Spiral placement for engrams
      const angle = _idx * 2.4;
      const radius = 2 + _idx * 0.5;
      const r = Math.floor(coreR + Math.sin(angle) * radius);
      const c = Math.floor(coreC + Math.cos(angle) * radius * 2); // *2 for character aspect ratio

      if (r >= 0 && r < GRID_ROWS && c >= 0 && c < GRID_COLS) {
        // Genesis Engram gets special treatment
        const isGenesis = engram.resonanceWeight > 1.6;
        newGrid[r][c] = {
          char: isGenesis ? '🜏' : 'Φ',
          color: isGenesis ? 'text-arkhe-orange animate-pulse drop-shadow-[0_0_5px_rgba(245,158,11,0.8)]' : 'text-arkhe-cyan'
        };
      }
    });

    // Render fContext (Immediate Context - Active Orbs)
    tzinor.fContext.forEach((node, _idx) => {
      // Map embedding to grid position
      const embX = node.embedding[0] || 0;
      const embY = node.embedding[1] || 0;

      const r = Math.floor(((embY + 1) / 2) * GRID_ROWS);
      const c = Math.floor(((embX + 1) / 2) * GRID_COLS);

      if (r >= 0 && r < GRID_ROWS && c >= 0 && c < GRID_COLS) {
        // Salience determines character density
        const charIdx = Math.floor(node.salience * (CHAR_PALETTE.length - 5)) + 4;
        const safeCharIdx = Math.max(0, Math.min(charIdx, CHAR_PALETTE.length - 1));

        let color = 'text-arkhe-cyan';
        if (threatLevel === 'critical') {color = 'text-arkhe-red';}
        else if (threatLevel === 'warning') {color = 'text-arkhe-orange';}

        newGrid[r][c] = {
          char: CHAR_PALETTE[safeCharIdx],
          color: `${color} drop-shadow-[0_0_3px_currentColor]`
        };
      }
    });

    setGrid(newGrid);
  }, [tzinor, threatLevel]);

  const terminalStyle = threatLevel === 'critical'
    ? 'border-arkhe-red/50 shadow-[0_0_20px_rgba(239,68,68,0.2)]'
    : threatLevel === 'warning'
    ? 'border-arkhe-orange/50 shadow-[0_0_15px_rgba(245,158,11,0.15)]'
    : 'border-[#1f2024]';

  const headerColor = threatLevel === 'critical'
    ? 'text-arkhe-red'
    : threatLevel === 'warning'
    ? 'text-arkhe-orange'
    : 'text-arkhe-muted';

  return (
    <motion.div
      initial={false}
      animate={{ borderColor: threatLevel === 'critical' ? '#ef4444' : threatLevel === 'warning' ? '#f59e0b' : '#1f2024' }}
      className={`bg-[#0a0a0c] border rounded-xl p-4 flex flex-col h-full relative overflow-hidden transition-shadow duration-500 ${terminalStyle}`}
    >
      {/* Scanline effect */}
      <div className="absolute inset-0 pointer-events-none bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] bg-[length:100%_4px,3px_100%] z-10 opacity-20"></div>

      <div className="flex items-center justify-between mb-4 border-b border-[#1f2024] pb-2 z-20">
        <h3 className={`font-mono text-xs uppercase tracking-widest ${headerColor} flex items-center gap-2`}>
          <Terminal className="w-3 h-3" />
          <span className={`w-2 h-2 rounded-full animate-pulse ${threatLevel === 'critical' ? 'bg-arkhe-red' : threatLevel === 'warning' ? 'bg-arkhe-orange' : 'bg-arkhe-cyan'}`}></span>
          Arkhe(n) Tzinor Terminal
        </h3>
        <div className="text-[10px] font-mono text-arkhe-muted flex items-center gap-4">
          <AnimatePresence mode="wait">
            <motion.span
              key={tzinor.lambdaCoherence}
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 5 }}
              className={threatLevel === 'critical' ? 'text-arkhe-red' : 'text-arkhe-cyan'}
            >
              λ₂: {tzinor.lambdaCoherence.toFixed(4)}
            </motion.span>
          </AnimatePresence>
          <span className="hidden md:inline opacity-50">ℂ × ℝ³ × ℤ → ℝ⁴</span>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center z-20">
        <motion.pre
          key={lastUpdate}
          initial={{ opacity: 0.8 }}
          animate={{ opacity: 1 }}
          className="font-mono text-[10px] sm:text-xs leading-none tracking-widest select-none"
        >
          {grid.map((row, rIdx) => (
            <div key={rIdx} className="flex">
              {row.map((cell, cIdx) => (
                <span key={`${rIdx}-${cIdx}`} className={`${cell.color} transition-colors duration-300`}>
                  {cell.char}
                </span>
              ))}
            </div>
          ))}
        </motion.pre>
      </div>

      <div className="mt-4 flex justify-between text-[10px] font-mono text-arkhe-muted z-20">
        <motion.span animate={{ color: threatLevel === 'critical' ? '#ef4444' : '#64748b' }}>
          fContext Nodes: {tzinor.fContext.length}
        </motion.span>
        <span>gMemory Engrams: {tzinor.gMemory.length}</span>
      </div>
    </motion.div>
  );
}
