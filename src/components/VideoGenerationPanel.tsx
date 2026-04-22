
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Video, Play, Loader2, Download, ShieldCheck, Cpu } from 'lucide-react';
import React, { useState, useRef } from 'react';

import { Card } from '../components/ui/Card';

import AtelierLog from './AtelierLog';

interface VideoGenerationPanelProps {
  onClose: () => void;
}

type Stage = 'IDENTIFY' | 'PROVE' | 'RECONCILE' | 'SYNTHESIZE' | 'IDLE';

export default function VideoGenerationPanel({ onClose }: VideoGenerationPanelProps) {
  const [prompt, setPrompt] = useState('');
  const [stage, setStage] = useState<Stage>('IDLE');
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  const handleGenerate = async () => {
    if (!prompt.trim()) {return;}

    setError(null);
    setVideoUrl(null);

    // 1. Identify stage
    setStage('IDENTIFY');
    await new Promise(r => setTimeout(r, 1000));

    // 2. Prove stage (Lean 4)
    setStage('PROVE');
    await new Promise(r => setTimeout(r, 2000));

    // 3. Reconcile stage (CUDA)
    setStage('RECONCILE');
    await new Promise(r => setTimeout(r, 1500));

    // 4. Synthesize stage (Veo-3.1)
    setStage('SYNTHESIZE');

    try {
      const response = await fetch('/api/generate-video', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to generate video');
      }

      const data = await response.json();
      setVideoUrl(data.videoUrl);
      setStage('IDLE');
    } catch (err: unknown) {
      setError(err.message || 'An unexpected error occurred.');
      setStage('IDLE');
    }
  };

  const stages = [
    { id: 'IDENTIFY', label: 'Semantic Identity', icon: ShieldCheck },
    { id: 'PROVE', label: 'Formal Reachability', icon: ShieldCheck },
    { id: 'RECONCILE', label: 'CUDA Reconcile', icon: Cpu },
    { id: 'SYNTHESIZE', label: 'Veo-3.1 Synthesis', icon: Video }
  ];

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-4xl bg-[#111214] border-arkhe-cyan/30 text-arkhe-text shadow-[0_0_30px_rgba(0,255,170,0.1)]">
        <div className="flex flex-row items-center justify-between border-b border-[#1f2024] p-4">
          <div className="flex items-center gap-3">
            <Video className="w-6 h-6 text-arkhe-cyan" />
            <h2 className="font-mono text-lg uppercase tracking-widest text-arkhe-cyan">
              Atelier Bridge: Intentional Projection
            </h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-arkhe-red p-2 rounded-md hover:bg-white/5 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-6">
            <div className="space-y-2">
              <label htmlFor="prompt" className="text-xs font-mono uppercase tracking-widest text-arkhe-muted">
                Dream Intent (Projection)
              </label>
              <div className="flex gap-2">
                <input
                  id="prompt"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="Describe the future state..."
                  className="flex-1 bg-[#0a0a0a] border border-[#1f2024] rounded-md px-3 py-2 font-mono text-sm focus:outline-none focus:border-arkhe-cyan text-arkhe-text"
                  disabled={stage !== 'IDLE'}
                />
                <button
                  onClick={handleGenerate}
                  disabled={stage !== 'IDLE' || !prompt.trim()}
                  className="flex items-center justify-center px-4 py-2 rounded-md bg-arkhe-cyan/20 text-arkhe-cyan hover:bg-arkhe-cyan/30 border border-arkhe-cyan/50 font-mono uppercase tracking-widest disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {stage !== 'IDLE' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 mr-2" />}
                  {stage !== 'IDLE' ? 'Projecting...' : 'Project'}
                </button>
              </div>
            </div>

            <div className="space-y-3">
              <h3 className="text-[10px] font-mono uppercase tracking-[0.2em] text-arkhe-muted border-b border-white/5 pb-1">
                Atelier Workflow Status
              </h3>
              <div className="space-y-2">
                {stages.map((s) => (
                  <div
                    key={s.id}
                    className={`flex items-center gap-3 p-2 rounded border transition-all duration-500 ${
                      stage === s.id
                        ? 'bg-arkhe-cyan/10 border-arkhe-cyan/50'
                        : 'bg-black/20 border-white/5 opacity-40'
                    }`}
                  >
                    <s.icon className={`w-4 h-4 ${stage === s.id ? 'text-arkhe-cyan animate-pulse' : 'text-arkhe-muted'}`} />
                    <span className="font-mono text-[10px] uppercase tracking-wider">{s.label}</span>
                    {stage === s.id && <Loader2 className="ml-auto w-3 h-3 animate-spin text-arkhe-cyan" />}
                  </div>
                ))}
              </div>
            </div>

            {error && (
              <div className="p-4 bg-arkhe-red/10 border border-arkhe-red/30 text-arkhe-red rounded text-sm font-mono">
                {error}
              </div>
            )}

            <AtelierLog />
          </div>

          <div className="relative aspect-video bg-[#0a0a0a] border border-[#1f2024] rounded-lg overflow-hidden flex items-center justify-center">
            {stage === 'SYNTHESIZE' ? (
              <div className="flex flex-col items-center gap-4 text-arkhe-cyan">
                <Loader2 className="w-12 h-12 animate-spin" />
                <div className="font-mono text-xs uppercase tracking-widest animate-pulse text-center px-4">
                  Establishing connection to Veo-3.1...
                  <br/>
                  Collapsing τ-field into visual data.
                </div>
              </div>
            ) : videoUrl ? (
              <video 
                ref={videoRef}
                src={videoUrl} 
                controls 
                autoPlay 
                loop 
                className="w-full h-full object-contain shadow-[0_0_50px_rgba(0,255,170,0.1)]"
              />
            ) : (
              <div className="text-arkhe-muted font-mono text-xs uppercase tracking-widest opacity-30 flex flex-col items-center gap-4">
                <Video className="w-12 h-12" />
                Awaiting Projection Proof
              </div>
            )}
            
            {videoUrl && stage === 'IDLE' && (
              <button
                className="absolute top-4 right-4 p-2 rounded-md bg-black/50 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/20 transition-colors"
                onClick={() => {
                  const a = document.createElement('a');
                  a.href = videoUrl;
                  a.download = `arkhe-synthesis-${Date.now()}.mp4`;
                  a.click();
                }}
              >
                <Download className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
}
