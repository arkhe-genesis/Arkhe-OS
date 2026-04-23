
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { cn } from '../../lib/utils';

interface BadgeProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'outline' | 'solid' | 'glass';
  color?: 'cyan' | 'amber' | 'fissure' | 'cerenkov' | 'omega';
}

export const Badge = ({ children, className, variant = 'outline', color = 'cyan' }: BadgeProps) => {
  const colorMap = {
    cyan: 'text-arkhe-cyan border-arkhe-cyan/50 bg-arkhe-cyan/10',
    amber: 'text-arkhe-amber border-arkhe-amber/50 bg-arkhe-amber/10',
    fissure: 'text-arkhe-fissure border-arkhe-fissure/50 bg-arkhe-fissure/10',
    cerenkov: 'text-arkhe-cerenkov border-arkhe-cerenkov/50 bg-arkhe-cerenkov/10',
    omega: 'text-white border-white/50 bg-white/10',
  };

  return (
    <span className={cn(
      "px-1.5 py-0.5 rounded font-mono text-[8px] uppercase tracking-widest border transition-all",
      colorMap[color],
      variant === 'glass' && "backdrop-blur-sm",
      className
    )}>
      {children}
    </span>
  );
};
