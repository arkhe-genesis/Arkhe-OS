/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Play, Pause, Square, Radio, Shield, Zap, Globe, Clock, Rewind, FastForward } from 'lucide-react';
import React, { useState, useEffect, useRef } from 'react';
// @ts-ignore
/* eslint-disable @typescript-eslint/no-explicit-any */


import { X, Video, Activity, Wifi, ShieldAlert, Play, Pause, Maximize, Volume2, VolumeX, Terminal, Eye, Layers } from 'lucide-react';
import { motion } from 'motion/react';
import React, { useEffect, useRef, useState } from 'react';
import shaka from 'shaka-player';

interface TemporalStreamViewerProps {
  onClose: () => void;
  streamId?: string;
}

export default function TemporalStreamViewer({ onClose, streamId = 'ARKHE-O-01' }: TemporalStreamViewerProps) {
export default function TemporalStreamViewer({ onClose }: TemporalStreamViewerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [player, setPlayer] = useState<unknown>(null);
  const [stats, setStats] = useState<Record<string, unknown>>({});
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLive, setIsLive] = useState(true);
  const [coherence, setCoherence] = useState(0.992);
  const [latencyMs, setLatencyMs] = useState(42);
  const [logs, setLogs] = useState<string[]>([]);
  const [activeChannel, setActiveChannel] = useState('PNT-1');

  const videoRef = useRef<HTMLVideoElement>(null);
  const playerRef = useRef<any>(null);

  const addLog = (msg: string) => {
    setLogs(prev => [`[${new Date().toISOString().split('T')[1].slice(0, 8)}] ${msg}`, ...prev].slice(0, 5));
  };

  useEffect(() => {
    if (!videoRef.current) return;
    if (!videoRef.current) {
      return;
    }

    shaka.polyfill.installAll();

    if (shaka.Player.isBrowserSupported()) {
      const player = new shaka.Player(videoRef.current);
      playerRef.current = player;

      player.addEventListener('error', (event: any) => {
        console.error('Shaka error:', event.detail);
        addLog(`STREAM ERROR: ${event.detail?.code}`);
      });

      // Load a sample stream (HLS/DASH)
      // For this demo, we'll just use a placeholder video if the URL fails
      const manifestUri = 'https://storage.googleapis.com/shaka-demo-assets/angel-one/dash.mpd';
      
      player.load(manifestUri).then(() => {
        addLog(`CONNECTED TO TEMPORAL STREAM: ${streamId}`);
        addLog('ZK-SYNC CHANNEL ESTABLISHED.');
      }).catch((e: any) => {
        addLog('FAILED TO LOAD MANIFEST. USING FALLBACK CHANNEL.');
      });
    }

    return () => {
      playerRef.current?.destroy();
    };
  }, [streamId]);

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
    } else {
      videoRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-md p-4">
      <div className="w-full max-w-5xl bg-[#0a0a0c] border border-[#7c3aed]/30 rounded-2xl shadow-[0_0_50px_rgba(124,58,237,0.2)] overflow-hidden flex flex-col aspect-video lg:aspect-auto lg:h-[80vh]">

        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[#7c3aed]/20 bg-[#7c3aed]/5">
          <div className="flex items-center gap-4">
            <Radio className="w-6 h-6 text-[#7c3aed] animate-pulse" />
            <div>
              <h2 className="text-lg font-bold text-white tracking-widest uppercase flex items-center gap-2">
                TEMPORAL STREAM: {streamId}
                {isLive && <span className="text-[10px] bg-red-600 text-white px-2 py-0.5 rounded-full animate-pulse ml-2">LIVE</span>}
              </h2>
              <div className="text-[10px] font-mono text-arkhe-muted">Quantum Sync Mode: ZK-STARK v2 // Coherence: {coherence.toFixed(4)}</div>
            </div>
          </div>
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-4 text-xs font-mono">
                <div className="flex flex-col items-end">
                    <span className="text-arkhe-muted text-[10px] uppercase">Latency</span>
                    <span className="text-[#00d4ff]">{latencyMs}ms</span>
                </div>
                <div className="flex flex-col items-end">
                    <span className="text-arkhe-muted text-[10px] uppercase">Channel</span>
                    <span className="text-[#7c3aed]">{activeChannel}</span>
                </div>
            </div>
            <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
              <X className="w-6 h-6" />
            </button>
      const newPlayer = new shaka.Player(videoRef.current);
      setPlayer(newPlayer);

      newPlayer.addEventListener('error', (event: any) => {
        const detail = event.detail;
        logger.error(`Error code ${detail.code} object ${JSON.stringify(detail)}`);
        setError(`SHAKA_ERR_${detail.code}`);
      });

      // Adaptation events -> Coherence changes
      newPlayer.addEventListener('adaptation', () => {
        const tracks = newPlayer.getVariantTracks();
        const activeTrack = tracks.find((t) => t.active);
        if (activeTrack) {
          // Estimate coherence based on bandwidth
          const newCoherence = Math.min(1.0, activeTrack.bandwidth / 5000000);
          setCoherence(newCoherence);
        }
      });

      // Segment downloaded -> Perception frame ready (simulated)
      newPlayer.addEventListener('segmentdownloaded', (_event: unknown) => {
        setCapturedFrames(prev => prev + 1);
      });

      // Configure for multiversal streaming
      newPlayer.configure({
        manifest: {
          dash: {
            ignoreSuggestedPresentationDelay: false,
          }
        },
        streaming: {
          lowLatencyMode: true,
          bufferingGoal: Math.max(10, 30 * coherence),
        }
      });

      // Using the official Shaka Project "Angel One" sci-fi asset for the temporal stream
      const manifestUri = 'https://storage.googleapis.com/shaka-demo-assets/angel-one/dash.mpd';

      void newPlayer.load(manifestUri).then(() => {
        logger.info('The video has now been loaded!');
        if (videoRef.current) {
          videoRef.current.muted = true;
          void videoRef.current.play()
            .then(() => setIsPlaying(true))
            .catch((_e: unknown) => logger.error("Auto-play prevented"));
        }
        return null;
      }).catch((e: any) => {
        logger.error('Error loading video: ' + e);
        setError(`LOAD_ERR_${e?.code || 'UNKNOWN'}`);
        return null;
      });

      const statTimer = setInterval(() => {
        setStats(newPlayer.getStats() as Record<string, unknown>);
      }, 1000);

      return () => {
        clearInterval(statTimer);
        void newPlayer.destroy();
      };
    } else {
      setError('BROWSER_UNSUPPORTED');
    }
    return () => {
      logger.info("TemporalStreamViewer cleanup");
    };
  }, [coherence]);

  const toggleVrMode = () => {
    if (player) {
      const newVrMode = !vrMode;
      (player as any).configure({
        vr: {
          motionPrediction: newVrMode,
        }
      });
      setVrMode(newVrMode);
      logger.info(`🜏 [PERCEPTION] VR Exploration Mode ${newVrMode ? 'ENABLED' : 'DISABLED'}.`);
    }
  };

  const captureFrame = () => {
    if (videoRef.current && canvasRef.current) {
      const canvas = canvasRef.current;
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.drawImage(videoRef.current, 0, 0);
        const frameData = canvas.toDataURL('image/jpeg', 0.8);

        // Dispatch event for Ouroboros Engine
        const event = new CustomEvent('ouroboros-frame-capture', {
          detail: {
            frameData,
            timestamp: Date.now(),
            source: 'Shaka Perception Adapter'
          }
        });
        window.dispatchEvent(event);

        setIsFlashing(true);
        setTimeout(() => setIsFlashing(false), 300);

        logger.info('🜏 [PERCEPTION] Frame captured for Ouroboros analysis.');
      }
    }
  };

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        void videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  const toggleFullscreen = () => {
    if (videoRef.current) {
      if (videoRef.current.requestFullscreen) {
        void videoRef.current.requestFullscreen();
      }
    }
  };

  const formatBitrate = (bits: number | undefined) => {
    if (!bits) {return '0 Mbps';}
    return (bits / 1000000).toFixed(2) + ' Mbps';
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/90 backdrop-blur-md">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-[#0a0a0c] border border-cyan-500/30 rounded-xl w-full max-w-5xl overflow-hidden shadow-[0_0_40px_rgba(6,182,212,0.15)] flex flex-col"
      >
        <div className="p-3 border-b border-cyan-500/20 flex justify-between items-center bg-cyan-500/5 shrink-0">
          <div className="flex items-center gap-3">
            <Video className="w-5 h-5 text-cyan-400" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-cyan-400 font-bold">
              Shaka-Protocol: Temporal Stream Viewer
            </h2>
            <span className="px-2 py-0.5 bg-cyan-500/20 text-cyan-400 text-[10px] font-mono rounded border border-cyan-500/30 animate-pulse">
              LIVE
            </span>
          </div>
        </div>

        <div className="flex flex-1 overflow-hidden">

          {/* Main Content Area */}
          <div className="flex-1 flex flex-col relative bg-black">
            <video
              ref={videoRef}
              className="w-full h-full object-contain"
              poster="https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&q=80&w=2000"
            />

            {/* Overlay Controls */}
            <div className="absolute inset-x-0 bottom-0 p-6 bg-gradient-to-t from-black to-transparent opacity-0 hover:opacity-100 transition-opacity">
               <div className="flex flex-col gap-4">
                  {/* Progress Bar */}
                  <div className="h-1 bg-white/10 rounded-full overflow-hidden group cursor-pointer">
                      <div className="h-full bg-[#7c3aed] w-3/4 group-hover:bg-[#a855f7] transition-colors"></div>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <button onClick={togglePlay} className="text-white hover:text-[#7c3aed] transition-colors">
                            {isPlaying ? <Pause className="w-6 h-6 fill-current" /> : <Play className="w-6 h-6 fill-current" />}
                        </button>
                        <button className="text-white hover:text-[#7c3aed] transition-colors">
                            <Rewind className="w-5 h-5 fill-current" />
                        </button>
                        <button className="text-white hover:text-[#7c3aed] transition-colors">
                            <FastForward className="w-5 h-5 fill-current" />
                        </button>
                        <div className="text-xs font-mono text-white/70 ml-2">
                            00:42:14 / 01:00:00
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        <button className="text-white hover:text-[#7c3aed] transition-colors">
                            <Shield className="w-5 h-5" />
                        </button>
                        <button className="text-white hover:text-[#7c3aed] transition-colors">
                            <Globe className="w-5 h-5" />
                        </button>
                    </div>
                  </div>
               </div>
            </div>
          </div>

          {/* Sidebar Telemetry */}
          <div className="w-72 border-l border-[#7c3aed]/20 bg-[#0d0e12] p-4 flex flex-col gap-6 font-mono shrink-0 overflow-y-auto">

            <section>
                <h3 className="text-[10px] text-[#7c3aed] font-bold uppercase tracking-widest mb-3 flex items-center gap-2">
                    <Zap className="w-3 h-3" /> Signal Integrity
                </h3>
                <div className="space-y-3">
                    <div className="bg-black/40 border border-[#1f2024] p-2 rounded">
                        <div className="flex justify-between text-[10px] mb-1">
                            <span className="text-arkhe-muted">BITRATE</span>
                            <span className="text-white">4.2 Gbps</span>
                        </div>
                        <div className="h-1 bg-zinc-800 rounded-full overflow-hidden">
                            <div className="h-full bg-[#7c3aed] w-4/5"></div>
                        </div>
                    </div>
                    <div className="bg-black/40 border border-[#1f2024] p-2 rounded">
                        <div className="flex justify-between text-[10px] mb-1">
                            <span className="text-arkhe-muted">JITTER</span>
                            <span className="text-white">0.02 ms</span>
                        </div>
                        <div className="h-1 bg-zinc-800 rounded-full overflow-hidden">
                            <div className="h-full bg-[#00d4ff] w-1/5"></div>
                        </div>
                    </div>
        <div className="flex flex-col lg:flex-row h-[70vh]">
          {/* Main Video Area */}
          <div className="flex-1 relative bg-black flex flex-col justify-center border-r border-cyan-500/20 group">
            {error ? (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-red-500 font-mono">
                <ShieldAlert className="w-12 h-12 mb-4" />
                <p>STREAM DECOHERENCE DETECTED</p>
                <p className="text-xs opacity-70">{error}</p>
              </div>
            ) : (
              <>
                <video
                  ref={videoRef}
                  className={`w-full h-full object-contain ${vrMode ? 'scale-110' : ''} transition-transform duration-700`}
                  poster="https://storage.googleapis.com/shaka-demo-assets/angel-one/poster.jpg"
                />
                <canvas ref={canvasRef} className="hidden" />

                {/* Scanlines Overlay */}
                <div className="absolute inset-0 pointer-events-none bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] bg-[length:100%_4px,3px_100%] opacity-20"></div>

                {/* Capture Flash */}
                {isFlashing && (
                  <div className="absolute inset-0 bg-white/80 z-10 pointer-events-none animate-pulse"></div>
                )}

                {/* Custom Controls */}
                <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/90 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center gap-4">
                  <button onClick={togglePlay} className="text-white hover:text-cyan-400 transition-colors">
                    {isPlaying ? <Pause className="w-6 h-6" /> : <Play className="w-6 h-6" />}
                  </button>
                  <button onClick={toggleMute} className="text-white hover:text-cyan-400 transition-colors">
                    {isMuted ? <VolumeX className="w-6 h-6" /> : <Volume2 className="w-6 h-6" />}
                  </button>

                  <div className="flex-1"></div>

                  <button onClick={captureFrame} className="text-white hover:text-cyan-400 transition-colors" title="Capture Frame for Ouroboros">
                    <Eye className="w-5 h-5" />
                  </button>
                  <button onClick={toggleVrMode} className={`transition-colors ${vrMode ? 'text-cyan-400' : 'text-white hover:text-cyan-400'}`} title="Toggle VR Exploration Mode">
                    <Layers className="w-5 h-5" />
                  </button>

                  <div className="flex items-center gap-2 text-xs font-mono text-cyan-400/70 ml-2">
                    <Activity className="w-4 h-4" />
                    {stats.width as number}x{stats.height as number}
                  </div>

                  <button onClick={toggleFullscreen} className="text-white hover:text-cyan-400 transition-colors ml-2">
                    <Maximize className="w-5 h-5" />
                  </button>
                </div>
              </>
            )}
          </div>

          {/* Telemetry Sidebar */}
          <div className="w-full lg:w-80 bg-[#0a0a0c] p-4 flex flex-col gap-4 overflow-y-auto custom-scrollbar">
            <div className="space-y-4">
              <h3 className="font-mono text-[10px] uppercase tracking-widest text-arkhe-muted border-b border-arkhe-border pb-2 flex items-center gap-2">
                <Terminal className="w-3 h-3" />
                Stream Telemetry
              </h3>

              <div className="grid grid-cols-2 gap-2">
                <div className="bg-[#111214] border border-arkhe-border rounded p-2">
                  <div className="text-[9px] font-mono text-arkhe-muted uppercase">Bandwidth</div>
                  <div className="text-xs font-mono text-cyan-400">{formatBitrate(stats.estimatedBandwidth as number)}</div>
                </div>
                <div className="bg-[#111214] border border-arkhe-border rounded p-2">
                  <div className="text-[9px] font-mono text-arkhe-muted uppercase">Resolution</div>
                  <div className="text-xs font-mono text-cyan-400">{(stats.width as number) || 0}x{(stats.height as number) || 0}</div>
                </div>
                <div className="bg-[#111214] border border-arkhe-border rounded p-2">
                  <div className="text-[9px] font-mono text-arkhe-muted uppercase">Coherence</div>
                  <div className="text-xs font-mono text-emerald-400">{(coherence * 100).toFixed(1)}%</div>
                </div>
                <div className="bg-[#111214] border border-arkhe-border rounded p-2">
                  <div className="text-[9px] font-mono text-arkhe-muted uppercase">Frames Captured</div>
                  <div className="text-xs font-mono text-amber-400">{capturedFrames}</div>
                </div>
              </div>

              <div className="bg-[#111214] border border-arkhe-border rounded p-3 space-y-2">
                <div className="text-[10px] font-mono text-arkhe-muted uppercase mb-2">Perception Layer Status</div>
                <div className="flex justify-between items-center border-b border-arkhe-border/50 pb-1">
                  <span className="text-[10px] font-mono text-arkhe-text">DASH Stream</span>
                  <span className="text-[10px] font-mono text-cyan-400">{stats.streamBandwidth ? formatBitrate(stats.streamBandwidth as number) : 'Auto'}</span>
                </div>
                <div className="flex justify-between items-center border-b border-arkhe-border/50 pb-1">
                  <span className="text-[10px] font-mono text-arkhe-text">VR Exploration</span>
                  <span className={`text-[10px] font-mono ${vrMode ? 'text-emerald-400' : 'text-arkhe-muted'}`}>{vrMode ? 'ENABLED' : 'DISABLED'}</span>
                </div>
            </section>

            <section className="flex-1">
                <h3 className="text-[10px] text-[#7c3aed] font-bold uppercase tracking-widest mb-3 flex items-center gap-2">
                    <Clock className="w-3 h-3" /> ZK-Sync Events
                </h3>
                <div className="space-y-2">
                    {logs.map((log, i) => (
                        <div key={i} className={`text-[9px] p-2 rounded border border-transparent ${i === 0 ? 'bg-[#7c3aed]/10 border-[#7c3aed]/20 text-[#7c3aed]' : 'text-arkhe-muted'}`}>
                            {log}
                        </div>
                    ))}
                </div>
            </section>

            <div className="mt-auto">
                <div className="p-3 bg-[#7c3aed]/5 border border-[#7c3aed]/20 rounded-lg text-center">
                    <div className="text-[9px] text-[#7c3aed] uppercase font-bold mb-1">Phase Locking</div>
                    <div className="text-xl font-bold text-white">θ = 0.0014</div>
                    <div className="text-[8px] text-arkhe-muted uppercase mt-1">Convergent</div>
                </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
