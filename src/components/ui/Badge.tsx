/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';

import { cn } from '../../lib/utils';

export const Badge = ({ children, className, variant }: { children: React.ReactNode, className?: string, variant?: any }) => (
  <span className={cn(
    "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
    variant === 'outline' ? "text-foreground" :
    variant === 'fissure' ? "border-arkhe-fissure text-arkhe-fissure bg-arkhe-fissure/10" :
    variant === 'cyan' ? "border-arkhe-cyan text-arkhe-cyan bg-arkhe-cyan/10" :
    variant === 'glass' ? "glass-hilbert" :
    "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
    className
  )}>{children}</span>
);
