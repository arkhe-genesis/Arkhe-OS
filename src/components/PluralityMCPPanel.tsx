
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { motion, AnimatePresence } from 'framer-motion';
import { Share2, Lock, Database, Zap, CheckCircle2, RefreshCw, ExternalLink } from 'lucide-react';
import React, { useState } from 'react';

interface PluralityMCPPanelProps {
  onClose: () => void;
}

export default function PluralityMCPPanel({ onClose }: PluralityMCPPanelProps) {
  const [step, setStep] = useState<'intro' | 'authorizing' | 'connected'>('intro');
  const [activeTab, setActiveTab] = useState<'status' | 'tools' | 'logs'>('status');
  const [logs, setLogs] = useState<string[]>([]);

  const addLog = (msg: string) => {
    setLogs(prev => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev].slice(0, 50));
  };

  const handleConnect = async () => {
    setStep('authorizing');
    addLog('Initiating Plurality OAuth handshake...');

    // Simulate OAuth flow
    setTimeout(() => {
      addLog('Redirecting to plurality.network for user authorization...');
      setTimeout(async () => {
        addLog('Authorization code received. Exchanging for access token...');

        try {
          const res = await fetch('/api/mcp/connect-plurality', { method: 'POST' });
          const data = await res.json();

          if (data.success) {
            addLog('Access token verified. MCP Session established.');
            addLog('Plurality Tools discovered: get_user_memory_buckets, query_social_graph');
            setStep('connected');
          } else {
            addLog('ERR_RES: 430 Security Rejection - ' + data.error);
            setStep('intro');
          }
        } catch (_e) {
          addLog('ERR_RES: 522 Connection Timed Out - Failed to reach backend substrate.');
          setStep('intro');
        }
      }, 1500);
    }, 1000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        className="w-full max-w-2xl bg-arkhe-card border border-arkhe-cyan/30 rounded-xl overflow-hidden shadow-[0_0_30px_rgba(0,255,170,0.1)] flex flex-col max-h-[80vh]"
      >
        {/* Header */}
        <div className="p-4 border-b border-arkhe-border flex items-center justify-between bg-arkhe-cyan/5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-arkhe-cyan/20 rounded-lg">
              <Share2 className="w-5 h-5 text-arkhe-cyan" />
            </div>
            <div>
              <h2 className="text-sm font-bold uppercase tracking-widest text-arkhe-text">Plurality Network // MCP Bridge</h2>
              <p className="text-[10px] font-mono text-arkhe-cyan/60 uppercase">Sovereign Social Graph & Memory Buckets</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-arkhe-muted hover:text-white transition-colors font-mono text-xs"
          >
            [X] CLOSE
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 font-mono text-xs">
          <AnimatePresence mode="wait">
            {step === 'intro' && (
              <motion.div
                key="intro"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="space-y-6"
              >
                <div className="bg-white/5 border border-white/10 p-4 rounded-lg space-y-3">
                  <p className="text-arkhe-text leading-relaxed">
                    Integrate your <span className="text-arkhe-cyan">Plurality Network</span> identity and data buckets directly into the Arkhe ecosystem via the Model Context Protocol (MCP).
                  </p>
                  <ul className="space-y-2 text-arkhe-muted">
                    <li className="flex items-center gap-2">
                      <Lock className="w-3 h-3 text-arkhe-cyan" />
                      <span>OAuth-secured access to social graphs</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <Database className="w-3 h-3 text-arkhe-cyan" />
                      <span>Distributed user memory buckets</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <Zap className="w-3 h-3 text-arkhe-cyan" />
                      <span>Context-aware tool invocation</span>
                    </li>
                  </ul>
                </div>

                <div className="flex flex-col gap-3 items-center pt-4">
                  <button
                    onClick={handleConnect}
                    className="w-full py-3 bg-arkhe-cyan text-black font-bold uppercase tracking-widest rounded hover:bg-white transition-colors shadow-[0_0_15px_rgba(0,255,170,0.3)]"
                  >
                    Connect Plurality Node
                  </button>
                  <a
                    href="https://app.plurality.network/mcp"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-arkhe-muted hover:text-arkhe-cyan transition-colors"
                  >
                    <span>Visit Plurality Network</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </motion.div>
            )}

            {step === 'authorizing' && (
              <motion.div
                key="authorizing"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex flex-col items-center justify-center py-12 space-y-6"
              >
                <div className="relative">
                  <RefreshCw className="w-12 h-12 text-arkhe-cyan animate-spin" />
                  <div className="absolute inset-0 bg-arkhe-cyan blur-xl opacity-20 animate-pulse"></div>
                </div>
                <div className="text-center space-y-2">
                  <h3 className="text-arkhe-cyan font-bold uppercase tracking-tighter text-lg">Authorizing Handshake</h3>
                  <p className="text-arkhe-muted animate-pulse">Waiting for Plurality OAuth response...</p>
                </div>
              </motion.div>
            )}

            {step === 'connected' && (
              <motion.div
                key="connected"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="h-full flex flex-col space-y-4"
              >
                {/* Tabs */}
                <div className="flex gap-4 border-b border-arkhe-border pb-2">
                  <button
                    onClick={() => setActiveTab('status')}
                    className={`pb-1 px-1 transition-colors ${activeTab === 'status' ? 'text-arkhe-cyan border-b border-arkhe-cyan' : 'text-arkhe-muted hover:text-white'}`}
                  >
                    STATUS
                  </button>
                  <button
                    onClick={() => setActiveTab('tools')}
                    className={`pb-1 px-1 transition-colors ${activeTab === 'tools' ? 'text-arkhe-cyan border-b border-arkhe-cyan' : 'text-arkhe-muted hover:text-white'}`}
                  >
                    MCP TOOLS
                  </button>
                  <button
                    onClick={() => setActiveTab('logs')}
                    className={`pb-1 px-1 transition-colors ${activeTab === 'logs' ? 'text-arkhe-cyan border-b border-arkhe-cyan' : 'text-arkhe-muted hover:text-white'}`}
                  >
                    SESSION LOGS
                  </button>
                </div>

                <div className="flex-1 overflow-y-auto">
                  {activeTab === 'status' && (
                    <div className="space-y-4 pt-2">
                      <div className="flex items-center justify-between p-3 bg-arkhe-cyan/10 border border-arkhe-cyan/20 rounded">
                        <span className="text-arkhe-muted">Connection Status:</span>
                        <div className="flex items-center gap-2 text-arkhe-green">
                          <CheckCircle2 className="w-4 h-4" />
                          <span className="font-bold">ACTIVE / RESONANT</span>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="p-3 border border-arkhe-border rounded bg-black/20">
                          <div className="text-[10px] text-arkhe-muted uppercase mb-1">Server URL</div>
                          <div className="truncate text-arkhe-cyan">https://app.plurality.network/mcp</div>
                        </div>
                        <div className="p-3 border border-arkhe-border rounded bg-black/20">
                          <div className="text-[10px] text-arkhe-muted uppercase mb-1">Protocol Version</div>
                          <div className="text-arkhe-cyan">2024-11-05</div>
                        </div>
                      </div>
                    </div>
                  )}

                  {activeTab === 'tools' && (
                    <div className="space-y-2 pt-2">
                      {[
                        { name: 'get_user_memory_buckets', desc: 'Retrieve encrypted memory buckets for the authorized user.' },
                        { name: 'query_social_graph', desc: 'Map social relations across decentralised identifiers.' },
                        { name: 'write_context_fragment', desc: 'Commit a new memory fragment to the Plurality storage layer.' }
                      ].map(tool => (
                        <div key={tool.name} className="p-3 border border-arkhe-border rounded bg-black/20 hover:border-arkhe-cyan/30 transition-colors group">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-arkhe-cyan font-bold">{tool.name}</span>
                            <Zap className="w-3 h-3 text-arkhe-cyan opacity-0 group-hover:opacity-100 transition-opacity" />
                          </div>
                          <p className="text-[10px] text-arkhe-muted leading-tight">{tool.desc}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {activeTab === 'logs' && (
                    <div className="space-y-1 pt-2 font-mono text-[10px]">
                      {logs.map((log, i) => (
                        <div key={i} className="text-arkhe-muted border-l border-arkhe-cyan/30 pl-2">
                          {log}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-arkhe-border bg-black/40 text-[9px] flex justify-between items-center text-arkhe-muted uppercase tracking-tighter">
          <span>Encrypted Tunnel: Plurality-Arkhe-Aegis</span>
          <span className="animate-pulse">Handshake 256-bit AES</span>
        </div>
      </motion.div>
    </div>
  );
}
