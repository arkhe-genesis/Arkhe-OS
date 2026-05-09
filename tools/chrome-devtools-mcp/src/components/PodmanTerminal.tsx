
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { motion } from 'motion/react';
import React, { useEffect, useState, useRef } from 'react';

interface PodmanTerminalProps {
  onClose: () => void;
}

const deploymentLogs = [
  "🜏 ═══════════════════════════════════════════════════════════════════════",
  "🜏 ARKHE(N) DEPLOYMENT - PODMAN NATIVE",
  "🜏 Date: 2026-03-14 15:14:15 UTC",
  "🜏 ═══════════════════════════════════════════════════════════════════════",
  "",
  "🜏 Creating directory structure...",
  "mkdir: created directory '/var/lib/arkhe/phase'",
  "mkdir: created directory '/var/lib/arkhe/tor'",
  "mkdir: created directory '/var/lib/arkhe/postgres'",
  "mkdir: created directory '/var/lib/arkhe/redis'",
  "",
  "🜏 Creating secrets...",
  "Writing db-password...",
  "Writing web3-provider...",
  "Writing contract-address...",
  "",
  "🜏 Deploying with podman play kube...",
  "Playing arkhe-pod.yaml...",
  "Pod arkhe-main created",
  "Container arkhe-core started",
  "Container arkhe-api started",
  "Container arkhe-frontend started",
  "Container postgres started",
  "Container redis started",
  "Container tor started",
  "",
  "Playing services-pod.yaml...",
  "Pod arkhe-services created",
  "Container payments started",
  "Container notifications started",
  "Container analytics started",
  "",
  "Playing industrial-pod.yaml...",
  "Pod arkhe-industrial created",
  "Container modbus-bridge started",
  "Container kona-stabilizer started",
  "",
  "🜏 Waiting for services to be ready...",
  "...",
  "...",
  "",
  "🜏 Health checks:",
  "Core: ONLINE (λ₂ = 1.618034)",
  "API: ONLINE",
  "Frontend: ONLINE",
  "",
  "🜏 ═══════════════════════════════════════════════════════════════════════",
  "🜏 DEPLOYMENT COMPLETE",
  "🜏 ",
  "🜏 Pods:",
  "POD ID        NAME              STATUS      CONTAINERS",
  "a1b2c3d4e5f6  arkhe-main        Running     6",
  "b2c3d4e5f6a1  arkhe-services    Running     3",
  "c3d4e5f6a1b2  arkhe-industrial  Running     2",
  "🜏 ",
  "🜏 Tor Hidden Services:",
  "🜏   API: arkhe3q2v...onion",
  "🜏   Tzinor: tzinor7x9...onion",
  "🜏 ",
  "🜏 Arkhe Protocol v1.0 is now operational in Rootless Daemonless mode.",
  "🜏 ═══════════════════════════════════════════════════════════════════════"
];

export default function PodmanTerminal({ onClose }: PodmanTerminalProps) {
  const [logs, setLogs] = useState<string[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let i = 0;
    const interval = setInterval(() => {
      if (i < deploymentLogs.length) {
        setLogs(prev => [...prev, deploymentLogs[i]]);
        i++;
        if (scrollRef.current) {
          scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
      } else {
        clearInterval(interval);
      }
    }, 150); // Speed of log appearance

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4 md:p-8 backdrop-blur-md">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="w-full max-w-4xl h-[80vh] bg-[#050505] border border-arkhe-cyan/40 rounded-lg shadow-[0_0_40px_rgba(0,255,255,0.1)] flex flex-col overflow-hidden"
      >
        <div className="flex justify-between items-center p-4 border-b border-arkhe-cyan/30 bg-arkhe-cyan/10">
          <div className="flex items-center gap-3">
            <span className="text-arkhe-cyan animate-pulse">⎈</span>
            <h2 className="text-arkhe-cyan font-mono font-bold tracking-widest text-sm md:text-base">PODMAN :: ARKHE(N) DEPLOYMENT</h2>
          </div>
          <button
            onClick={onClose}
            className="text-arkhe-cyan/70 hover:text-arkhe-cyan font-mono text-sm tracking-wider transition-colors"
          >
            [ CLOSE ]
          </button>
        </div>

        <div
          ref={scrollRef}
          className="p-6 overflow-y-auto flex-1 font-mono text-xs md:text-sm text-arkhe-cyan/90 whitespace-pre-wrap leading-relaxed"
          style={{ textShadow: '0 0 5px rgba(0,255,255,0.3)' }}
        >
          {logs.map((log, index) => (
            <div key={index}>{log}</div>
          ))}
          <span className="animate-pulse inline-block w-2 h-4 bg-arkhe-cyan ml-1 align-middle mt-1"></span>
        </div>
      </motion.div>
    </div>
  );
}
