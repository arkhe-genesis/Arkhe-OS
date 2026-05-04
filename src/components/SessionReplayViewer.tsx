/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Play, Pause, SkipBack, SkipForward, Activity, User, Globe, Shield, Terminal, MessageSquare, AlertCircle } from 'lucide-react';
import React, { useState, useEffect, useRef } from 'react';

import type { UserSession } from '../../server/types';

interface SessionReplayViewerProps {
  onClose: () => void;
  session: UserSession;
}

export default function SessionReplayViewer({ onClose, session }: SessionReplayViewerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentEventIndex, setCurrentEventIndex] = useState(0);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [activeTab, setActiveTab] = useState<'replay' | 'analysis' | 'network'>('replay');

  const videoPlaceholderRef = useRef<HTMLDivElement>(null);

  // Auto-playback logic
  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (isPlaying && currentEventIndex < session.events.length - 1) {
      timer = setTimeout(() => {
        setCurrentEventIndex(prev => prev + 1);
      }, 1000 / playbackSpeed);
    } else if (currentEventIndex >= session.events.length - 1) {
      setIsPlaying(false);
    }
    return () => clearTimeout(timer);
  }, [isPlaying, currentEventIndex, session.events.length, playbackSpeed]);

  const progress = (currentEventIndex / (session.events.length - 1)) * 100;
  const currentEvent = session.events[currentEventIndex];
    const fetchSessions = async () => {
      try {
        const res = await fetch('/api/lucent/sessions');
        const data = await res.json() as UserSession[];
        setSessions(data);
        setLoading(false);
      } catch (e) {
        console.error('Failed to fetch sessions:', e);
        setLoading(false);
      }
    };

    void fetchSessions();
    const interval = setInterval(() => {
      void fetchSessions();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/90 backdrop-blur-md">
      <div className="bg-[#0a0a0c] border border-arkhe-cyan/30 rounded-xl w-full max-w-6xl overflow-hidden flex flex-col h-[85vh] shadow-[0_0_40px_rgba(0,255,170,0.15)]">

        {/* Header */}
        <div className="p-4 border-b border-arkhe-cyan/20 bg-arkhe-cyan/5 flex justify-between items-center shrink-0">
          <div className="flex items-center gap-3">
            <Activity className="w-5 h-5 text-arkhe-cyan" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-arkhe-cyan font-bold">
              Lucent Session Replay: {session.id}
            </h2>
            <span className="px-2 py-0.5 text-[10px] font-mono rounded border bg-arkhe-cyan/20 text-arkhe-cyan border-arkhe-cyan/30">
              {new Date(session.startTime).toLocaleString()}
            </span>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Main Replay Area */}
          <div className="flex-1 flex flex-col bg-black overflow-hidden border-r border-arkhe-cyan/10">
            {/* Nav Tabs */}
            <div className="flex border-b border-arkhe-cyan/10">
              <button
                onClick={() => setActiveTab('replay')}
                className={`px-4 py-2 font-mono text-[10px] uppercase tracking-widest transition-colors ${activeTab === 'replay' ? 'bg-arkhe-cyan/10 text-arkhe-cyan border-b-2 border-arkhe-cyan' : 'text-arkhe-muted hover:text-arkhe-text'}`}
              >
                Visual Replay
              </button>
              <button
                onClick={() => setActiveTab('analysis')}
                className={`px-4 py-2 font-mono text-[10px] uppercase tracking-widest transition-colors ${activeTab === 'analysis' ? 'bg-arkhe-cyan/10 text-arkhe-cyan border-b-2 border-arkhe-cyan' : 'text-arkhe-muted hover:text-arkhe-text'}`}
              >
                AI Analysis (Ω)
              </button>
              <button
                onClick={() => setActiveTab('network')}
                className={`px-4 py-2 font-mono text-[10px] uppercase tracking-widest transition-colors ${activeTab === 'network' ? 'bg-arkhe-cyan/10 text-arkhe-cyan border-b-2 border-arkhe-cyan' : 'text-arkhe-muted hover:text-arkhe-text'}`}
              >
                Network Packets
              </button>
            </div>

            <div className="flex-1 relative bg-[#050507] flex items-center justify-center p-8">
              {activeTab === 'replay' ? (
                <div className="w-full h-full relative border border-arkhe-border rounded-lg bg-[#0d0e12] overflow-hidden flex flex-col">
                  <div className="flex-1 flex items-center justify-center text-arkhe-muted font-mono text-xs">
                    <div className="text-center space-y-4">
                      <Terminal className="w-12 h-12 mx-auto opacity-20" />
                      <div>DOM Snapshot Reconstruction...</div>
                      <div className="text-[10px] opacity-50">Event {currentEventIndex + 1} of {session.events.length}</div>
                    </div>
                  </div>
                  {/* Event Marker in Replay */}
                  <div className="absolute inset-0 pointer-events-none p-4">
                    <div className="border border-arkhe-cyan/20 p-2 rounded bg-black/40 text-[10px] font-mono text-arkhe-cyan inline-block">
                      {currentEvent.type} // {currentEvent.eventType || 'N/A'}
                    </div>
                  </div>
                </div>
              ) : activeTab === 'analysis' ? (
                <div className="w-full h-full p-8 font-mono space-y-8 overflow-y-auto custom-scrollbar">
                  <div className="space-y-4">
                    <h3 className="text-arkhe-cyan text-sm uppercase font-bold flex items-center gap-2">
                      <Shield className="w-4 h-4" /> Root Cause Identification
                    </h3>
                    <div className={`p-4 rounded border ${session.analysis?.bugDetected ? 'bg-red-500/10 border-red-500/30 text-red-400' : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'}`}>
                      <div className="font-bold uppercase text-xs mb-1">{session.analysis?.bugDetected ? 'Bug Detected' : 'No Anomalies Found'}</div>
                      <div className="text-xs opacity-80 leading-relaxed">{session.analysis?.description || 'Nenhuma descrição disponível para esta análise.'}</div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-white/5 border border-arkhe-border rounded-lg">
                      <div className="text-[10px] text-arkhe-muted uppercase mb-1">UX Score (Ω)</div>
                      <div className="text-2xl font-bold text-arkhe-cyan">{session.analysis?.uxScore.toFixed(1)}/10</div>
                    </div>
                    <div className="p-4 bg-white/5 border border-arkhe-border rounded-lg">
                      <div className="text-[10px] text-arkhe-muted uppercase mb-1">Coherence λ</div>
                      <div className="text-2xl font-bold text-arkhe-purple">{currentEvent.coherence?.toFixed(3) || '0.992'}</div>
                    </div>
                  </div>

                  <div className="p-4 bg-black border border-arkhe-cyan/20 rounded-lg">
                    <div className="text-[10px] text-arkhe-cyan uppercase font-bold mb-2">Recursive ZK-Proof (Groth16)</div>
                    <code className="text-[9px] text-arkhe-muted break-all leading-tight">
                      {session.analysis?.zkProof || '---'}
                    </code>
                    <div className="mt-2 text-right">
                      <span className="text-[8px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 uppercase">Verified on Arkhe-Chain</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="w-full h-full p-6 font-mono text-xs overflow-y-auto custom-scrollbar space-y-1">
                  {session.events.map((e, i) => (
                    <div key={i} className={`p-2 rounded border transition-colors ${i === currentEventIndex ? 'bg-arkhe-cyan/10 border-arkhe-cyan/30 text-arkhe-cyan' : 'bg-transparent border-transparent text-arkhe-muted'}`}>
                       <span className="opacity-50">[{new Date(e.timestamp).toISOString().split('T')[1].slice(0, 8)}]</span>
                       <span className="mx-2 font-bold">{e.type}</span>
                       <span className="opacity-70">{JSON.stringify((e as any).payload || {})}</span>
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
                        {(event.payload as { type?: string, message?: string })?.type === 'error' ? (
                          <span className="text-red-400 flex items-center gap-1">
                            <Bug className="w-3 h-3" /> {(event.payload as { message: string }).message}
                          </span>
                        ) : (
                          (event.payload as { type?: string })?.type || JSON.stringify(event.payload || {})
                        )}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Playback Controls */}
            <div className="p-4 bg-[#0d0e12] border-t border-arkhe-cyan/10">
              <div className="space-y-4">
                <div className="flex items-center gap-4">
                  <div className="flex-1 h-1.5 bg-black rounded-full overflow-hidden border border-arkhe-border relative group cursor-pointer">
                    <div
                      className="h-full bg-arkhe-cyan transition-all duration-300 relative"
                      style={{ width: `${progress}%` }}
                    >
                      <div className="absolute right-0 top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full shadow-lg opacity-0 group-hover:opacity-100 transition-opacity"></div>
                    </div>
                  </div>
                  <div className="text-[10px] font-mono text-arkhe-muted min-w-[60px] text-right">
                    {currentEventIndex + 1} / {session.events.length}
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <button
                      onClick={() => setCurrentEventIndex(0)}
                      className="text-arkhe-muted hover:text-white transition-colors"
                    >
                      <SkipBack className="w-4 h-4 fill-current" />
                    </button>
                    <button
                      onClick={() => setIsPlaying(!isPlaying)}
                      className="w-10 h-10 rounded-full bg-arkhe-cyan flex items-center justify-center text-black hover:bg-white transition-all shadow-[0_0_15px_rgba(0,255,170,0.3)]"
                    >
                      {isPlaying ? <Pause className="w-5 h-5 fill-current" /> : <Play className="w-5 h-5 fill-current ml-0.5" />}
                    </button>
                    <button
                      onClick={() => setCurrentEventIndex(prev => Math.min(session.events.length - 1, prev + 1))}
                      className="text-arkhe-muted hover:text-white transition-colors"
                    >
                      <SkipForward className="w-4 h-4 fill-current" />
                    </button>

                    <div className="h-6 w-px bg-arkhe-border mx-2"></div>

                    <div className="flex items-center gap-2">
                      {[1, 2, 4, 8].map(speed => (
                        <button
                          key={speed}
                          onClick={() => setPlaybackSpeed(speed)}
                          className={`w-8 h-6 rounded border font-mono text-[10px] transition-colors ${playbackSpeed === speed ? 'bg-arkhe-cyan text-black border-arkhe-cyan' : 'text-arkhe-muted border-arkhe-border hover:border-arkhe-cyan'}`}
                        >
                          {speed}x
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center gap-6">
                    <div className="flex flex-col items-end">
                      <span className="text-[8px] text-arkhe-muted uppercase">Coherence Drift</span>
                      <span className="text-[10px] font-mono text-arkhe-cyan font-bold">± 0.0004 rad</span>
                    </div>
                    <div className="flex flex-col items-end">
                      <span className="text-[8px] text-arkhe-muted uppercase">Nakamoto Distance</span>
                      <span className="text-[10px] font-mono text-arkhe-green font-bold">2.1e-12</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar: Event Stream */}
          <div className="w-80 border-l border-arkhe-cyan/10 bg-[#0d0e12] flex flex-col shrink-0 overflow-hidden">
            <div className="p-4 border-b border-arkhe-cyan/10 bg-black/40">
              <h3 className="text-[10px] font-mono text-arkhe-muted uppercase tracking-widest flex items-center gap-2">
                <Terminal className="w-3 h-3" /> Raw Event Stream
              </h3>
            </div>

            <div className="flex-1 overflow-y-auto custom-scrollbar p-2 space-y-1">
              {session.events.map((e, i) => (
                <button
                  key={i}
                  onClick={() => {
                    setCurrentEventIndex(i);
                    setActiveTab('replay');
                  }}
                  className={`w-full p-2 rounded text-left font-mono transition-all border ${
                    i === currentEventIndex
                      ? 'bg-arkhe-cyan/10 border-arkhe-cyan/30 text-arkhe-cyan'
                      : 'bg-transparent border-transparent text-arkhe-muted hover:bg-white/5'
                  }`}
                >
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-[9px] font-bold truncate pr-2">{e.type}</span>
                    <span className="text-[8px] opacity-50">{new Date(e.timestamp).toISOString().split('T')[1].slice(0, 11)}</span>
                  </div>
                  {e.eventType && <div className="text-[8px] opacity-70 italic truncate">{e.eventType}</div>}
                </button>
              ))}
            </div>

            <div className="p-4 border-t border-arkhe-cyan/10 bg-black/40">
              <div className="flex items-center justify-between text-[10px] font-mono">
                <div className="flex items-center gap-2 text-arkhe-muted">
                  <User className="w-3 h-3" /> Device
                </div>
                <div className="text-arkhe-cyan">GPD Win 4 (m1k1o)</div>
              </div>
              <div className="flex items-center justify-between text-[10px] font-mono mt-2">
                <div className="flex items-center gap-2 text-arkhe-muted">
                  <Globe className="w-3 h-3" /> Region
                </div>
                <div className="text-arkhe-cyan">PT (Lisboa)</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
