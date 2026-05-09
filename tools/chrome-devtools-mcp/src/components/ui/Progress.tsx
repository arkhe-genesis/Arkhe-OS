
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
}

export const Progress = ({ value, className, color = 'cyan' }: ProgressProps) => {
  const colorMap = {
    cyan: 'bg-arkhe-cyan',
    cerenkov: 'bg-arkhe-cerenkov',
    amber: 'bg-arkhe-amber',
    fissure: 'bg-arkhe-fissure',
  };

  return (
    <div className={cn("w-full bg-white/10 rounded-full h-2", className)}>
      <div
        className={cn("h-full rounded-full transition-all duration-500", colorMap[color])}
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  );
};
