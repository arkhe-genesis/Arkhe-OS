
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { cn } from '../../lib/utils';

interface ProgressProps {
  value: number;
  className?: string;
  color?: 'cyan' | 'cerenkov' | 'amber' | 'fissure';
  showLabel?: boolean;
}

export const Progress = ({
  value,
  className,
  color = 'cyan',
  showLabel = false
}: ProgressProps) => {
  const colorMap = {
    cyan: 'bg-arkhe-cyan shadow-[0_0_8px_rgba(0,229,255,0.4)]',
    cerenkov: 'bg-arkhe-cerenkov shadow-[0_0_8px_rgba(0,127,255,0.4)]',
    amber: 'bg-arkhe-amber shadow-[0_0_8px_rgba(245,158,11,0.4)]',
    fissure: 'bg-arkhe-fissure shadow-[0_0_8px_rgba(225,29,72,0.4)]',
  };

  const clampedValue = Math.min(Math.max(value, 0), 100);

  return (
    <div className={cn("w-full space-y-1", className)}>
      {showLabel && (
        <div className="flex justify-between text-[8px] font-mono uppercase tracking-tighter text-arkhe-muted">
          <span>Coherence</span>
          <span>{clampedValue.toFixed(1)}%</span>
        </div>
      )}
      <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden border border-white/5">
        <div
          className={cn("h-full transition-all duration-700 ease-out", colorMap[color])}
          style={{ width: `${clampedValue}%` }}
        />
      </div>
    </div>
  );
};
