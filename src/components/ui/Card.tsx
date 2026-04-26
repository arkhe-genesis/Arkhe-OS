
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { motion } from 'framer-motion';
import React from 'react';

import { cn } from '../../lib/utils';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  status?: 'normal' | 'warning' | 'critical' | 'omega';
  variant?: 'liquid' | 'hilbert' | 'base';
  className?: string;
  children?: React.ReactNode;
}

export function Card({
  className,
  title,
  icon,
  action,
  status = 'normal',
  variant = 'base',
  children,
  ..._props
}: CardProps) {
  const isLiquid = variant === 'liquid';
  const isHilbert = variant === 'hilbert';

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ scale: 1.005 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
      className={cn(
        "rounded-xl overflow-hidden flex flex-col relative transition-all duration-300",
        variant === 'base' && "bg-arkhe-card border border-arkhe-border",
        isLiquid && "glass-liquid",
        isHilbert && "glass-hilbert kerning-fibonacci",
        status === 'warning' && "border-arkhe-amber/50 shadow-[0_0_15px_rgba(245,158,11,0.1)]",
        status === 'critical' && "border-arkhe-fissure/50 shadow-[0_0_15px_rgba(225,29,72,0.1)] fissure-glow",
        status === 'omega' && "border-arkhe-omega/50 shadow-[0_0_20px_rgba(255,255,255,0.2)]",
        className
      )}
    >
      {/* Decorative Fissure (Error) */}
      {status === 'critical' && (
        <div className="absolute top-0 left-0 w-full h-full pointer-events-none opacity-20">
          <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
            <path d="M0,20 L30,40 L10,60 L50,80 L40,100" stroke="var(--color-arkhe-fissure)" fill="none" strokeWidth="0.5" />
          </svg>
        </div>
      )}

      {status === 'warning' && <div className="absolute top-0 left-0 w-full h-0.5 bg-arkhe-amber animate-pulse" />}
      {status === 'omega' && <div className="absolute top-0 left-0 w-full h-0.5 bg-arkhe-omega" />}

      {(title || icon || action) && (
        <div className={cn(
          "px-4 py-3 border-b flex items-center justify-between",
          variant === 'base' ? "bg-black/20 border-arkhe-border" : "border-white/5 bg-white/5"
        )}>
          <div className="flex items-center gap-2">
            {icon && <div className="text-arkhe-muted">{icon}</div>}
            {title && (
              <h3 className={cn(
                "font-mono text-golden-xs uppercase tracking-widest",
                isHilbert ? "text-arkhe-cerenkov" : "text-arkhe-muted"
              )}>
                {title}
              </h3>
            )}
          </div>
          {action && <div className="flex items-center">{action}</div>}
        </div>
      )}
      <div className="p-4 flex-1 flex flex-col relative z-10">
        {children}
      </div>
    </motion.div>
  );
}

export function CardHeader({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn("px-4 py-3 border-b border-white/5 bg-white/5", className)}>{children}</div>;
}

export function CardTitle({ children, className }: { children: React.ReactNode; className?: string }) {
  return <h3 className={cn("font-mono text-golden-xs uppercase tracking-widest text-arkhe-muted", className)}>{children}</h3>;
}

export function CardContent({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn("p-4", className)}>{children}</div>;
}
