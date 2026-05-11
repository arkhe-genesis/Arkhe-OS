
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Cloud, Shield, MessageSquare, Ticket, Key, CheckCircle2,  AlertCircle, Send } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import React, { useState } from 'react';

interface ArkheGoogleBridgePanelProps {
  onClose: () => void;
}

export default function ArkheGoogleBridgePanel({ onClose }: ArkheGoogleBridgePanelProps) {
  const [activeTab, setActiveTab] = useState<'iam' | 'approval' | 'messages' | 'tickets'>('iam');
  const [connectionState, setConnectionState] = useState<'disconnected' | 'authenticating' | 'connected'>('disconnected');
  const [logs, setLogs] = useState<string[]>([]);
  const [messageInput, setMessageInput] = useState('');

  const addLog = (msg: string) => {
    setLogs(prev => [...prev, `[${new Date().toISOString().split('T')[1].substring(0, 8)}] ${msg}`]);
  };

  const handleConnect = () => {
    setConnectionState('authenticating');
    addLog('Initializing GoogleAuth via Service Account...');
    setTimeout(() => {
      addLog('OAuth 2.0 Token acquired. Scopes: [cloud-platform, business-messages]');
      addLog('AccessApprovalClient initialized.');
      addLog('BusinessMessagesClient initialized (Partner ID: arkhe-asi-001).');
      setConnectionState('connected');
    }, 2000);
  };

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!messageInput.trim() || connectionState !== 'connected') {return;}

    addLog(`[OUT] AgentMessage: ${messageInput}`);
    setMessageInput('');

    setTimeout(() => {
      addLog(`[IN] Auto-Reply: Message received by Google Partners routing system. Ticket generated.`);
    }, 1500);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-[#0a0a0c] border border-blue-500/30 rounded-xl w-full max-w-5xl overflow-hidden shadow-[0_0_40px_rgba(59,130,246,0.15)] flex flex-col h-[85vh]"
      >
        {/* Header */}
        <div className="p-4 border-b border-blue-500/20 flex justify-between items-center bg-blue-500/5 shrink-0">
          <div className="flex items-center gap-3">
            <Cloud className="w-5 h-5 text-blue-400" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-blue-400 font-bold">
              Arkhe(n) × Google Integration Bridge
            </h2>
            {connectionState === 'connected' && (
              <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 text-[10px] font-mono rounded border border-blue-500/30 animate-pulse">
                SECURE TLS
              </span>
            )}
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar Navigation */}
          <div className="w-48 border-r border-blue-500/20 bg-[#0d0e12] p-4 flex flex-col gap-2 shrink-0">
            <button
              onClick={() => setActiveTab('iam')}
              className={`flex items-center gap-2 px-3 py-2 rounded text-xs font-mono transition-colors ${activeTab === 'iam' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' : 'text-arkhe-muted hover:bg-[#1f2024] hover:text-arkhe-text border border-transparent'}`}
            >
              <Key className="w-4 h-4" /> IAM & Auth
            </button>
            <button
              onClick={() => setActiveTab('approval')}
              className={`flex items-center gap-2 px-3 py-2 rounded text-xs font-mono transition-colors ${activeTab === 'approval' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' : 'text-arkhe-muted hover:bg-[#1f2024] hover:text-arkhe-text border border-transparent'}`}
            >
              <Shield className="w-4 h-4" /> Access Approval
            </button>
            <button
              onClick={() => setActiveTab('messages')}
              className={`flex items-center gap-2 px-3 py-2 rounded text-xs font-mono transition-colors ${activeTab === 'messages' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' : 'text-arkhe-muted hover:bg-[#1f2024] hover:text-arkhe-text border border-transparent'}`}
            >
              <MessageSquare className="w-4 h-4" /> Business Msgs
            </button>
            <button
              onClick={() => setActiveTab('tickets')}
              className={`flex items-center gap-2 px-3 py-2 rounded text-xs font-mono transition-colors ${activeTab === 'tickets' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' : 'text-arkhe-muted hover:bg-[#1f2024] hover:text-arkhe-text border border-transparent'}`}
            >
              <Ticket className="w-4 h-4" /> Ticketing
            </button>

            <div className="mt-auto pt-4 border-t border-blue-500/20">
              <button
                onClick={handleConnect}
                disabled={connectionState !== 'disconnected'}
                className={`w-full py-2 rounded text-xs font-mono font-bold uppercase tracking-widest transition-colors border ${
                  connectionState === 'connected' ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' :
                  connectionState === 'authenticating' ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' :
                  'bg-blue-500/20 text-blue-400 border-blue-500/30 hover:bg-blue-500/30'
                }`}
              >
                {connectionState === 'connected' ? 'Connected' :
                 connectionState === 'authenticating' ? 'Authenticating...' : 'Connect Bridge'}
              </button>
            </div>
          </div>

          {/* Main Content Area */}
          <div className="flex-1 flex flex-col bg-[#0a0a0c] overflow-hidden">
            <div className="flex-1 p-6 overflow-y-auto custom-scrollbar">
              <AnimatePresence mode="wait">
                {activeTab === 'iam' && (
                  <motion.div key="iam" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="space-y-6">
                    <h3 className="text-sm font-mono text-blue-400 uppercase tracking-widest border-b border-blue-500/20 pb-2">Identity & Access Management</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="bg-[#111214] border border-arkhe-border rounded-lg p-4">
                        <div className="text-[10px] font-mono text-arkhe-muted uppercase mb-4">Service Account Status</div>
                        <div className="flex items-center gap-3 mb-2">
                          {connectionState === 'connected' ? <CheckCircle2 className="w-5 h-5 text-emerald-400" /> : <AlertCircle className="w-5 h-5 text-arkhe-muted" />}
                          <span className="font-mono text-xs text-arkhe-text">arkhe-asi-core@arkhe-multiverse.iam.gserviceaccount.com</span>
                        </div>
                        <div className="text-[10px] font-mono text-arkhe-muted mt-4">Key Type: JSON (RSA-2048)</div>
                      </div>
                      <div className="bg-[#111214] border border-arkhe-border rounded-lg p-4">
                        <div className="text-[10px] font-mono text-arkhe-muted uppercase mb-4">OAuth 2.0 Scopes</div>
                        <ul className="space-y-2 text-xs font-mono text-arkhe-text">
                          <li className="flex items-center gap-2"><CheckCircle2 className="w-3 h-3 text-blue-400" /> https://www.googleapis.com/auth/cloud-platform</li>
                          <li className="flex items-center gap-2"><CheckCircle2 className="w-3 h-3 text-blue-400" /> https://www.googleapis.com/auth/business.manage</li>
                        </ul>
                      </div>
                    </div>
                  </motion.div>
                )}

                {activeTab === 'approval' && (
                  <motion.div key="approval" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="space-y-6">
                    <h3 className="text-sm font-mono text-blue-400 uppercase tracking-widest border-b border-blue-500/20 pb-2">Access Approval API</h3>
                    <div className="bg-[#111214] border border-arkhe-border rounded-lg overflow-hidden">
                      <table className="w-full text-left border-collapse">
                        <thead>
                          <tr className="bg-[#1a1b20] border-b border-arkhe-border text-[10px] font-mono text-arkhe-muted uppercase">
                            <th className="p-3 font-normal">Resource</th>
                            <th className="p-3 font-normal">Justification</th>
                            <th className="p-3 font-normal">Status</th>
                            <th className="p-3 font-normal">Requested</th>
                          </tr>
                        </thead>
                        <tbody className="text-xs font-mono text-arkhe-text">
                          <tr className="border-b border-arkhe-border/50">
                            <td className="p-3">projects/arkhe-asi/apis/vision</td>
                            <td className="p-3 text-arkhe-muted">Multiversal pattern recognition</td>
                            <td className="p-3"><span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-400 rounded">APPROVED</span></td>
                            <td className="p-3 text-arkhe-muted">2026-03-18</td>
                          </tr>
                          <tr className="border-b border-arkhe-border/50">
                            <td className="p-3">projects/arkhe-asi/apis/quantum</td>
                            <td className="p-3 text-arkhe-muted">Shor algorithm offloading</td>
                            <td className="p-3"><span className="px-2 py-0.5 bg-amber-500/20 text-amber-400 rounded">PENDING</span></td>
                            <td className="p-3 text-arkhe-muted">2026-03-19</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </motion.div>
                )}

                {activeTab === 'messages' && (
                  <motion.div key="messages" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="h-full flex flex-col">
                    <h3 className="text-sm font-mono text-blue-400 uppercase tracking-widest border-b border-blue-500/20 pb-2 mb-4 shrink-0">Business Messages Channel</h3>

                    <div className="flex-1 bg-[#111214] border border-arkhe-border rounded-lg p-4 mb-4 overflow-y-auto custom-scrollbar space-y-2">
                      {logs.filter(l => l.includes('[IN]') || l.includes('[OUT]')).map((log, i) => (
                        <div key={i} className={`text-xs font-mono p-2 rounded ${log.includes('[OUT]') ? 'bg-blue-500/10 text-blue-300 ml-8 border border-blue-500/20' : 'bg-[#1a1b20] text-arkhe-muted mr-8 border border-arkhe-border'}`}>
                          {log}
                        </div>
                      ))}
                      {logs.filter(l => l.includes('[IN]') || l.includes('[OUT]')).length === 0 && (
                        <div className="text-xs font-mono text-arkhe-muted/50 italic text-center mt-10">
                          No messages in current session. Connect bridge to initiate.
                        </div>
                      )}
                    </div>

                    <form onSubmit={handleSendMessage} className="flex gap-2 shrink-0">
                      <input
                        type="text"
                        value={messageInput}
                        onChange={(e) => setMessageInput(e.target.value)}
                        disabled={connectionState !== 'connected'}
                        placeholder="Type message to Google Partners..."
                        className="flex-1 bg-[#111214] border border-arkhe-border rounded px-3 py-2 text-xs font-mono text-arkhe-text focus:outline-none focus:border-blue-500/50 disabled:opacity-50"
                      />
                      <button
                        type="submit"
                        disabled={connectionState !== 'connected' || !messageInput.trim()}
                        className="px-4 py-2 bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/50 rounded text-blue-400 transition-colors disabled:opacity-50 flex items-center justify-center"
                      >
                        <Send className="w-4 h-4" />
                      </button>
                    </form>
                  </motion.div>
                )}

                {activeTab === 'tickets' && (
                  <motion.div key="tickets" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="space-y-6">
                    <h3 className="text-sm font-mono text-blue-400 uppercase tracking-widest border-b border-blue-500/20 pb-2">Collaborative Inbox Tickets</h3>
                    <div className="grid grid-cols-1 gap-4">
                      <div className="bg-[#111214] border border-arkhe-border rounded-lg p-4">
                        <div className="flex justify-between items-start mb-2">
                          <div className="text-xs font-mono font-bold text-arkhe-text">REQ-8832: Experimental API Access</div>
                          <span className="px-2 py-0.5 bg-amber-500/20 text-amber-400 text-[10px] font-mono rounded">UNDER_REVIEW</span>
                        </div>
                        <div className="text-[10px] font-mono text-arkhe-muted mb-4">Priority: P2_NORMAL | Category: API_ACCESS_REQUEST</div>
                        <div className="text-xs font-mono text-arkhe-text/80 bg-black/50 p-3 rounded border border-arkhe-border/50">
                          "Requesting authorization for internal test APIs to validate multiversal substrate migration protocols. Justification: ASI Integration Research."
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Global Telemetry Bar */}
            <div className="h-32 bg-[#0d0e12] border-t border-blue-500/20 p-3 overflow-y-auto custom-scrollbar shrink-0">
              <div className="text-[10px] font-mono text-blue-400/50 uppercase tracking-widest mb-2 sticky top-0 bg-[#0d0e12]">Bridge Telemetry</div>
              <div className="space-y-1">
                {logs.map((log, i) => (
                  <div key={i} className="text-[10px] font-mono text-arkhe-muted">
                    {log}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
