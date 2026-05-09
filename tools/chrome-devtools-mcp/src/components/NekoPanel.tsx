/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { motion } from 'framer-motion';
import { X, Monitor, Activity, Shield, ExternalLink, RefreshCw } from 'lucide-react';
import { useState, useEffect } from 'react';

interface NekoPanelProps {
  onClose: () => void;
  roomId?: string;
}

export default function NekoPanel({ onClose, roomId = 'Arkhe-Alpha' }: NekoPanelProps) {
  const [status, setStatus] = useState({
    cpu: 0,
    mem: 0,
    fps: 0,
    users: 1,
    latency: 0,
    connected: false,
  });

  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false);
      setStatus({
        cpu: 12.4,
        mem: 416,
        fps: 30,
        users: 1,
        latency: 14,
        connected: true,
      });
    }, 2000);

    const interval = setInterval(() => {
      setStatus(prev => ({
        ...prev,
        cpu: +(prev.cpu + (Math.random() * 2 - 1)).toFixed(1),
        latency: Math.floor(prev.latency + (Math.random() * 4 - 2)),
      }));
    }, 3000);

    return () => {
      clearTimeout(timer);
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        className="bg-[#0a0e17] border border-arkhe-cyan/30 rounded-xl w-full max-w-6xl h-[85vh] overflow-hidden shadow-[0_0_50px_rgba(0,255,170,0.15)] flex flex-col"
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-arkhe-border flex justify-between items-center bg-arkhe-cyan/5">
          <div className="flex items-center gap-4">
            <div className="p-2 bg-arkhe-cyan/10 rounded-lg">
              <Monitor className="w-5 h-5 text-arkhe-cyan" />
            </div>
            <div>
              <h2 className="font-mono text-sm font-bold uppercase tracking-widest text-white">
                Neko Virtual Browser <span className="text-arkhe-cyan">// {roomId}</span>
              </h2>
              <div className="flex items-center gap-2 mt-1">
                <span className={`w-1.5 h-1.5 rounded-full ${status.connected ? 'bg-arkhe-green animate-pulse' : 'bg-arkhe-orange'}`}></span>
                <span className="text-[10px] font-mono text-arkhe-muted uppercase tracking-tighter">
                  {status.connected ? 'WebRTC Stream Active (Pion)' : 'Establishing Link...'}
                </span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <button className="p-2 text-arkhe-muted hover:text-white transition-colors">
              <RefreshCw className="w-4 h-4" />
            </button>
            <button onClick={onClose} className="p-2 text-arkhe-muted hover:text-white transition-colors">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Main Viewport */}
          <div className="flex-1 bg-black relative flex items-center justify-center group">
            {isLoading ? (
              <div className="flex flex-col items-center gap-4">
                <Activity className="w-12 h-12 text-arkhe-cyan animate-spin" />
                <div className="font-mono text-xs text-arkhe-cyan uppercase tracking-widest">Synchronizing Phase...</div>
              </div>
            ) : (
              <div className="w-full h-full relative">
                {/* Simulated Iframe / WebRTC View */}
                <div className="absolute inset-0 bg-zinc-900 flex items-center justify-center">
                   <img
                    src="https://neko.m1k1o.net/img/intro.gif"
                    alt="Neko Stream"
                    className="w-full h-full object-cover opacity-40 grayscale"
                   />
                   <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent"></div>
                   <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center space-y-4">
                      <ExternalLink className="w-12 h-12 text-arkhe-cyan mx-auto opacity-50" />
                      <p className="text-xs font-mono text-arkhe-muted max-w-xs">
                        Neko environment ready. Interactive WebRTC overlay stabilized on Sheet #2026.
                      </p>
                      <button className="px-6 py-2 border border-arkhe-cyan text-arkhe-cyan text-xs font-mono hover:bg-arkhe-cyan hover:text-black transition-all uppercase tracking-widest">
                        Initialize Control
                      </button>
                   </div>
                </div>

                {/* Overlays */}
                <div className="absolute top-4 left-4 flex gap-2">
                  <div className="px-2 py-1 bg-black/60 border border-white/10 rounded font-mono text-[9px] text-white flex items-center gap-2">
                    <div className="w-1 h-1 bg-red-500 rounded-full animate-pulse"></div>
                    LIVE REC
                  </div>
                  <div className="px-2 py-1 bg-black/60 border border-white/10 rounded font-mono text-[9px] text-white">
                    1920x1080 @ {status.fps}FPS
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Sidebar Telemetry */}
          <div className="w-64 border-l border-arkhe-border bg-[#0d1117] p-6 space-y-8 flex flex-col">
            <section className="space-y-4">
              <h3 className="text-[10px] font-mono text-arkhe-muted uppercase tracking-widest border-b border-arkhe-border pb-2">Stream Metrics</h3>
              <div className="grid grid-cols-1 gap-4">
                <div className="space-y-1">
                  <div className="flex justify-between text-[10px] font-mono text-arkhe-muted uppercase">
                    <span>CPU Load</span>
                    <span className="text-white">{status.cpu}%</span>
                  </div>
                  <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-arkhe-cyan"
                      initial={{ width: 0 }}
                      animate={{ width: `${status.cpu}%` }}
                    />
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="flex justify-between text-[10px] font-mono text-arkhe-muted uppercase">
                    <span>Memory</span>
                    <span className="text-white">{status.mem}MB</span>
                  </div>
                  <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-arkhe-cyan"
                      initial={{ width: 0 }}
                      animate={{ width: '40%' }}
                    />
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Activity className="w-3 h-3 text-arkhe-cyan" />
                    <span className="text-[10px] font-mono text-arkhe-muted uppercase">Latency</span>
                  </div>
                  <span className="text-[10px] font-mono text-arkhe-green font-bold">{status.latency}ms</span>
                </div>
              </div>
            </section>

            <section className="space-y-4">
              <h3 className="text-[10px] font-mono text-arkhe-muted uppercase tracking-widest border-b border-arkhe-border pb-2">Active Entities</h3>
              <div className="space-y-2">
                <div className="flex items-center justify-between p-2 bg-white/5 border border-white/5 rounded">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-arkhe-cyan rounded-full"></div>
                    <span className="text-[10px] font-mono text-white">Operator-01</span>
                  </div>
                  <Shield className="w-3 h-3 text-arkhe-cyan" />
                </div>
                <div className="flex items-center justify-center p-4 border border-dashed border-white/10 rounded">
                  <span className="text-[9px] font-mono text-arkhe-muted uppercase">Waiting for peers...</span>
                </div>
              </div>
            </section>

            <section className="space-y-4 flex-1">
              <h3 className="text-[10px] font-mono text-arkhe-muted uppercase tracking-widest border-b border-arkhe-border pb-2">Log</h3>
              <div className="text-[9px] font-mono text-arkhe-muted space-y-1 max-h-40 overflow-y-auto custom-scrollbar">
                <div className="text-arkhe-green">[0.00] Pion-WebRTC Stack Init</div>
                <div className="text-arkhe-green">[0.42] ICE Gathering Complete</div>
                <div className="text-arkhe-green">[1.12] DTLS Handshake Verified</div>
                <div>[1.15] DataChannel opened (control)</div>
                <div>[1.16] MediaStream attached (vp8)</div>
                <div className="animate-pulse">_</div>
              </div>
            </section>

            <div className="pt-4 border-t border-arkhe-border">
              <button className="w-full py-2 bg-arkhe-cyan/10 border border-arkhe-cyan/30 text-arkhe-cyan text-[10px] font-mono uppercase tracking-widest hover:bg-arkhe-cyan hover:text-black transition-all">
                Copy Invitation Link
              </button>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
