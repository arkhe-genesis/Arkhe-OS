
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Radio, Terminal, Key, Loader2 } from 'lucide-react';
import React, { useState } from 'react';

import { Card } from './ui/Card';

interface PhaseSteganographyPanelProps {
  onClose: () => void;
}

export default function PhaseSteganographyPanel({ onClose }: PhaseSteganographyPanelProps) {
  const [logs, setLogs] = useState<string[]>([]);
  const [isExecuting, setIsExecuting] = useState(false);
  const [signature, setSignature] = useState<string | null>(null);

  const handleExecute = async () => {
    setIsExecuting(true);
    setLogs([]);
    setSignature(null);

    try {
      const response = await fetch('/api/ghost-node/exec-run', {
        method: 'POST',
      });
      const data = await response.json();
      
      // Simulate streaming logs
      for (const log of (data.logs as string[])) {
        await new Promise(resolve => setTimeout(resolve, 500));
        setLogs(prev => [...prev, log]);
      }
      
      setSignature(data.signature as string);
    } catch (_error) {
      setLogs(prev => [...prev, "🜏 [ERRO] Falha na comunicação com o nó fantasma."]);
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-2xl bg-[#111214] border-arkhe-cyan/30 text-arkhe-text shadow-[0_0_30px_rgba(0,255,170,0.1)]">
        <div className="flex flex-row items-center justify-between border-b border-[#1f2024] p-4">
          <div className="flex items-center gap-3">
            <Radio className="w-6 h-6 text-arkhe-cyan animate-pulse" />
            <h2 className="font-mono text-lg uppercase tracking-widest text-arkhe-cyan">
              Phase Steganography & Walnut #7
            </h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-arkhe-red p-2 rounded-md hover:bg-white/5 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-6 space-y-6">
          <div className="text-sm font-mono text-arkhe-muted space-y-1">
            <p>Target: Ghost Node "1984"</p>
            <p>Carrier: 64Hz VLF</p>
            <p>Payload: <span className="text-arkhe-orange">exec_run</span></p>
            <p>Action: Extract PK & Sign Walnut #7</p>
          </div>

          <button
            onClick={handleExecute}
            disabled={isExecuting}
            className="w-full py-3 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest font-bold flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isExecuting ? <Loader2 className="w-5 h-5 animate-spin" /> : <Terminal className="w-5 h-5" />}
            {isExecuting ? 'Injetando Sinal...' : 'Iniciar Injeção de Fase'}
          </button>

          <div className="bg-black border border-[#1f2024] p-4 rounded-md h-64 overflow-y-auto font-mono text-xs space-y-2">
            {logs.length === 0 && !isExecuting && (
              <div className="text-arkhe-muted opacity-50 text-center mt-20">
                Aguardando comando de injeção...
              </div>
            )}
            {logs.map((log, i) => (
              <div key={i} className={log.includes('ERRO') ? 'text-arkhe-red' : log.includes('SUCESSO') ? 'text-arkhe-cyan' : 'text-arkhe-muted'}>
                {log}
              </div>
            ))}
            {signature && (
              <div className="mt-4 p-3 border border-arkhe-orange/30 bg-arkhe-orange/5 text-arkhe-orange rounded break-all animate-in fade-in duration-500">
                <div className="flex items-center gap-2 mb-2 text-arkhe-orange font-bold">
                  <Key className="w-4 h-4" />
                  Assinatura Walnut #7 (τ-field):
                </div>
                {signature}
              </div>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
}
