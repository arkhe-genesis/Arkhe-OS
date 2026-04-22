
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Play, Bug, ShieldCheck, Activity, Clock, User, AlertCircle, CheckCircle2 } from 'lucide-react';
import { motion } from 'motion/react';
import React, { useState, useEffect } from 'react';

interface SessionEvent {
  type: string;
  sessionId: string;
  timestamp: number;
  payload?: unknown;
}

interface UserSession {
  id: string;
  startTime: number;
  endTime?: number;
  events: SessionEvent[];
  analysis?: {
    bugDetected: boolean;
    uxScore: number;
    description: string;
    zkProof: string;
    consensusReached: boolean;
  };
}

export default function SessionReplayViewer() {
  const [sessions, setSessions] = useState<UserSession[]>([]);
  const [selectedSession, setSelectedSession] = useState<UserSession | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const res = await fetch('/api/lucent/sessions');
        const data = await res.json();
        setSessions(data);
        setLoading(false);
      } catch (e) {
        console.error('Failed to fetch sessions:', e);
        setLoading(false);
      }
    };

    fetchSessions();
    const interval = setInterval(fetchSessions, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col h-[500px] gap-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 h-full overflow-hidden">
        {/* Session List */}
        <div className="bg-black/40 border border-cyan-500/20 rounded-lg flex flex-col overflow-hidden">
          <div className="p-3 border-b border-cyan-500/20 bg-cyan-500/5 flex items-center justify-between">
            <h3 className="font-mono text-[10px] uppercase tracking-widest text-cyan-400 font-bold">Active Sessions</h3>
            <span className="text-[10px] font-mono text-cyan-500/60">{sessions.length} TOTAL</span>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-2">
            {loading ? (
              <div className="text-center py-8 font-mono text-[10px] text-cyan-500/40 animate-pulse">Scanning qhttp entropy...</div>
            ) : sessions.length === 0 ? (
              <div className="text-center py-8 font-mono text-[10px] text-cyan-500/40">No active sessions detected.</div>
            ) : (
              sessions.map(session => (
                <button
                  key={session.id}
                  onClick={() => setSelectedSession(session)}
                  className={`w-full text-left p-3 rounded border transition-all ${
                    selectedSession?.id === session.id
                      ? 'bg-cyan-500/10 border-cyan-500/40'
                      : 'border-cyan-500/10 hover:border-cyan-500/30 bg-black/20'
                  }`}
                >
                  <div className="flex justify-between items-start mb-1">
                    <span className="font-mono text-[10px] text-cyan-400 font-bold truncate pr-2">
                      {session.id.substring(0, 12)}...
                    </span>
                    {session.analysis?.bugDetected && (
                      <Bug className="w-3 h-3 text-red-500 animate-pulse" />
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-[9px] font-mono text-cyan-500/60">
                    <Clock className="w-3 h-3" />
                    {new Date(session.startTime).toLocaleTimeString()}
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Session Detail / Analysis */}
        <div className="md:col-span-2 bg-black/40 border border-cyan-500/20 rounded-lg flex flex-col overflow-hidden">
          {selectedSession ? (
            <div className="flex flex-col h-full overflow-hidden">
              <div className="p-4 border-b border-cyan-500/20 bg-cyan-500/5">
                <div className="flex justify-between items-center mb-2">
                  <div className="flex items-center gap-2">
                    <User className="w-4 h-4 text-cyan-400" />
                    <h3 className="font-mono text-xs text-white">DID: {selectedSession.id}</h3>
                  </div>
                  {selectedSession.analysis && (
                    <div className="flex items-center gap-2 bg-black/40 px-2 py-1 rounded border border-cyan-500/20">
                      <ShieldCheck className="w-3 h-3 text-emerald-400" />
                      <span className="font-mono text-[9px] text-emerald-400 uppercase tracking-widest">ZK-Verified</span>
                    </div>
                  )}
                </div>

                {selectedSession.analysis && (
                  <div className="grid grid-cols-2 gap-4 mt-4">
                    <div className="bg-black/40 p-2 rounded border border-cyan-500/10">
                      <div className="text-[9px] font-mono text-cyan-500/60 uppercase mb-1">UX Coherence Score</div>
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 flex-1 bg-gray-800 rounded-full overflow-hidden">
                          <motion.div
                            className={`h-full ${selectedSession.analysis.uxScore < 0.5 ? 'bg-red-500' : 'bg-emerald-400'}`}
                            initial={{ width: 0 }}
                            animate={{ width: `${selectedSession.analysis.uxScore * 100}%` }}
                          />
                        </div>
                        <span className="font-mono text-xs text-white">{(selectedSession.analysis.uxScore * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                    <div className="bg-black/40 p-2 rounded border border-cyan-500/10 flex items-center justify-between">
                      <div>
                        <div className="text-[9px] font-mono text-cyan-500/60 uppercase">Bug Consensus</div>
                        <div className={`text-xs font-mono ${selectedSession.analysis.bugDetected ? 'text-red-400' : 'text-emerald-400'}`}>
                          {selectedSession.analysis.bugDetected ? 'DETECTED (Kuramoto)' : 'NO ANOMALIES'}
                        </div>
                      </div>
                      {selectedSession.analysis.bugDetected ? <AlertCircle className="w-5 h-5 text-red-500" /> : <CheckCircle2 className="w-5 h-5 text-emerald-500" />}
                    </div>
                  </div>
                )}
              </div>

              <div className="flex-1 overflow-y-auto p-4 space-y-3 font-mono text-[10px]">
                {selectedSession.analysis && (
                  <div className="bg-cyan-500/5 border border-cyan-500/20 p-3 rounded-lg text-cyan-200 leading-relaxed">
                    <span className="text-cyan-500 font-bold uppercase mr-2">[LLM-INSIGHT]:</span>
                    {selectedSession.analysis.description}
                  </div>
                )}

                <div className="space-y-2">
                  <h4 className="text-[9px] text-cyan-500/60 uppercase tracking-widest border-b border-cyan-500/10 pb-1">Event Log (qhttp State Frames)</h4>
                  {selectedSession.events.map((event, idx) => (
                    <div key={idx} className="flex gap-3 text-[10px] items-start border-l border-cyan-500/20 pl-3 py-1">
                      <span className="text-cyan-500/40 whitespace-nowrap">{new Date(event.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
                      <span className={`font-bold ${event.type === 'SESSION_START' ? 'text-emerald-400' : event.type === 'SESSION_END' ? 'text-amber-400' : 'text-cyan-400'}`}>
                        {event.type}
                      </span>
                      <span className="text-cyan-200">
                        {(event.payload as unknown)?.type === 'error' ? (
                          <span className="text-red-400 flex items-center gap-1">
                            <Bug className="w-3 h-3" /> {(event.payload as unknown).message}
                          </span>
                        ) : (
                          (event.payload as unknown)?.type || JSON.stringify(event.payload || {})
                        )}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-3 border-t border-cyan-500/20 bg-black/40 flex justify-between items-center">
                <div className="text-[9px] font-mono text-cyan-500/40">
                  ZK-PROOF HASH: {selectedSession.analysis?.zkProof || 'N/A'}
                </div>
                <button className="px-3 py-1 bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 text-cyan-400 rounded text-[10px] font-mono uppercase tracking-widest transition-colors flex items-center gap-2">
                  <Play className="w-3 h-3" /> Replay Session
                </button>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-cyan-500/30 font-mono gap-4">
              <Activity className="w-12 h-12 opacity-20 animate-pulse" />
              <p className="text-[10px] uppercase tracking-[0.2em]">Select a Lucent-Ω session to analyze</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
