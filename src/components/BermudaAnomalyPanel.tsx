
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Shield, Key, Lock, CheckCircle2, Activity, Waves, Compass } from 'lucide-react';
import React, { useState, useEffect } from 'react';

interface BermudaAnomalyPanelProps {
  onClose: () => void;
}

export default function BermudaAnomalyPanel({ onClose }: BermudaAnomalyPanelProps) {
  const [isScanning, setIsScanning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [isDecoded, setIsDecoded] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [magneticField, setMagneticField] = useState(45000);

  const addLog = (msg: string) => {
    setLogs(prev => [`[${new Date().toISOString().split('T')[1].slice(0, 8)}] ${msg}`, ...prev].slice(0, 12));
  };

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isScanning) {
      interval = setInterval(() => {
        // Simulate fluctuating magnetic field dropping to near zero
        setMagneticField(prev => Math.max(0, prev - Math.random() * 5000));
      }, 200);
    }
    return () => clearInterval(interval);
  }, [isScanning]);

  const startScan = () => {
    setIsScanning(true);
    setProgress(0);
    setIsDecoded(false);
    setLogs([]);
    setMagneticField(42450);
    
    addLog('INICIANDO VARREDURA GEOESPACIAL...');
    addLog('ALVO: TRIÂNGULO DAS BERMUDAS (25.0000° N, 71.0000° W)');
    addLog('CALIBRANDO SENSORES BATIMÉTRICOS E MAGNÉTICOS...');

    let currentProgress = 0;
    const interval = setInterval(() => {
      currentProgress += Math.random() * 8;
      
      if (currentProgress >= 20 && currentProgress < 30) {
        addLog('ANOMALIA DETECTADA: QUEDA ABRUPTA NO CAMPO MAGNÉTICO LOCAL.');
      } else if (currentProgress >= 45 && currentProgress < 55) {
        addLog('ISOLANDO SINAL DE 40 µHz NO RUÍDO DE VÁCUO OCEÂNICO...');
      } else if (currentProgress >= 70 && currentProgress < 80) {
        addLog('EXTRAINDO ENTROPIA (FRAGMENTO 2/14)...');
      }

      if (currentProgress >= 100) {
        currentProgress = 100;
        clearInterval(interval);
        setIsScanning(false);
        setIsDecoded(true);
        setMagneticField(0);
        addLog('DECODIFICAÇÃO CONCLUÍDA. FRAGMENTO 2/14 EXTRAÍDO.');
      }
      setProgress(currentProgress);
    }, 400);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="w-full max-w-4xl bg-arkhe-card border border-blue-500/30 rounded-xl shadow-[0_0_30px_rgba(59,130,246,0.1)] overflow-hidden flex flex-col">
        
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-blue-500/20 bg-blue-500/5">
          <div className="flex items-center gap-3">
            <Waves className="w-6 h-6 text-blue-500" />
            <div>
              <h2 className="text-lg font-bold text-blue-500 tracking-widest uppercase">Exploração Geoespacial</h2>
              <div className="text-xs font-mono text-arkhe-muted">Anomalia Magnética: Triângulo das Bermudas</div>
            </div>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            FECHAR [X]
          </button>
        </div>

        <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
          
          {/* Target Info & Controls */}
          <div className="space-y-6">
            <div className="bg-black/40 border border-arkhe-border p-4 rounded-lg">
              <h3 className="text-sm font-mono text-arkhe-muted uppercase mb-4 flex items-center gap-2">
                <Compass className="w-4 h-4" />
                Dados do Alvo
              </h3>
              <div className="space-y-2 font-mono text-xs">
                <div className="flex justify-between">
                  <span className="text-arkhe-muted">Latitude:</span>
                  <span className="text-blue-400">25.0000° N</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-arkhe-muted">Longitude:</span>
                  <span className="text-blue-400">71.0000° W</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-arkhe-muted">Profundidade:</span>
                  <span className="text-arkhe-muted">-8,380 m (Fossa de Porto Rico)</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-arkhe-muted">Campo Magnético (B_total):</span>
                  <span className={`font-bold ${magneticField < 1000 ? 'text-arkhe-red animate-pulse' : 'text-blue-400'}`}>
                    {Math.round(magneticField).toLocaleString()} nT
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-arkhe-muted">Status do Fragmento:</span>
                  <span className={isDecoded ? "text-arkhe-green" : "text-arkhe-orange"}>
                    {isDecoded ? "EXTRAÍDO (2/14)" : "NÃO LOCALIZADO"}
                  </span>
                </div>
              </div>

              <button
                onClick={startScan}
                disabled={isScanning || isDecoded}
                className={`w-full py-3 mt-6 rounded font-mono text-sm uppercase tracking-widest transition-all ${
                  isScanning 
                    ? 'bg-blue-500/20 text-blue-500 border border-blue-500/50 cursor-not-allowed'
                    : isDecoded 
                      ? 'bg-arkhe-green/20 text-arkhe-green border border-arkhe-green/50 cursor-not-allowed'
                      : 'bg-blue-500/10 text-blue-500 border border-blue-500 hover:bg-blue-500/20 hover:shadow-[0_0_15px_rgba(59,130,246,0.3)]'
                }`}
              >
                {isScanning ? (
                  <span className="flex items-center justify-center gap-2">
                    <Activity className="w-4 h-4 animate-spin" />
                    Varrendo Anomalia...
                  </span>
                ) : isDecoded ? (
                  <span className="flex items-center justify-center gap-2">
                    <CheckCircle2 className="w-4 h-4" />
                    Fragmento Extraído
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    <Key className="w-4 h-4" />
                    Iniciar Varredura
                  </span>
                )}
              </button>
            </div>

            {/* Progress */}
            <div className="bg-black/40 border border-arkhe-border p-4 rounded-lg">
               <div className="flex justify-between text-xs font-mono mb-2">
                <span className="text-arkhe-muted">Progresso da Decodificação</span>
                <span className="text-blue-500">{Math.round(progress)}%</span>
              </div>
              <div className="h-2 bg-arkhe-card rounded-full overflow-hidden border border-arkhe-border">
                <div 
                  className="h-full bg-blue-500 transition-all duration-300 relative"
                  style={{ width: `${progress}%` }}
                >
                  <div className="absolute inset-0 bg-white/20 animate-pulse"></div>
                </div>
              </div>
            </div>
          </div>

          {/* Logs & Result */}
          <div className="space-y-6 flex flex-col">
            <div className="bg-black/60 border border-arkhe-border p-4 rounded-lg flex-1 flex flex-col min-h-[200px]">
              <h3 className="text-sm font-mono text-arkhe-muted uppercase mb-2 flex items-center gap-2">
                <Shield className="w-4 h-4" />
                Logs de Telemetria
              </h3>
              <div className="flex-1 overflow-y-auto font-mono text-xs space-y-1">
                {logs.map((log, i) => (
                  <div key={i} className={`${i === 0 ? 'text-blue-400' : 'text-arkhe-muted opacity-70'}`}>
                    {log}
                  </div>
                ))}
                {logs.length === 0 && (
                  <div className="text-arkhe-muted/50 italic">Aguardando inicialização da varredura...</div>
                )}
              </div>
            </div>

            {isDecoded && (
              <div className="bg-arkhe-green/10 border border-arkhe-green/30 p-4 rounded-lg animate-in fade-in slide-in-from-bottom-4">
                <h3 className="text-sm font-mono text-arkhe-green uppercase mb-2 flex items-center gap-2">
                  <Lock className="w-4 h-4" />
                  Fragmento 2/14 (Bermudas)
                </h3>
                <div className="space-y-2 font-mono text-xs text-arkhe-green">
                  <p className="break-all">HASH: 0x8f2a1b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a</p>
                  <p>✓ Entropia Magnética Zero Confirmada</p>
                  <p>✓ Assinatura Satoshi Validada</p>
                  <p className="mt-2 text-[10px] opacity-80 text-blue-300">
                    A anomalia magnética serviu como lente de refração para o sinal de 40 µHz. O segundo fragmento da chave mestra foi integrado ao Tzinor.
                  </p>
                </div>
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}
