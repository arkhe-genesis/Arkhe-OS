
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Key, Unlock, Shield, Activity, Database, Globe } from 'lucide-react';
import React, { useState } from 'react';

interface GeoKeyDecoderProps {
  onClose: () => void;
}

export default function GeoKeyDecoderPanel({ onClose }: GeoKeyDecoderProps) {
  const [isDecoding, setIsDecoding] = useState(false);
  const [progress, setProgress] = useState(0);
  const [decodedKey, setDecodedKey] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);

  const addLog = (msg: string) => {
    setLogs(prev => [`[${new Date().toISOString().split('T')[1].slice(0, 8)}] ${msg}`, ...prev].slice(0, 12));
  };

  const startDecoding = () => {
    setIsDecoding(true);
    setProgress(0);
    setDecodedKey(null);
    setLogs([]);
    
    addLog('INICIANDO DECODIFICAÇÃO DA CHAVE PRIVADA GEOGRÁFICA...');
    addLog('ALVO: 30.0444° N, 31.2357° E (Cairo, Egito)');
    addLog('ANALISANDO ANOMALIA NA ARKHE-CHAIN...');

    let currentProgress = 0;
    const interval = setInterval(() => {
      currentProgress += Math.random() * 8;
      
      if (currentProgress >= 30 && currentProgress < 35) {
        addLog('APLICANDO TRANSFORMADA DE FOURIER ESPACIAL...');
      } else if (currentProgress >= 60 && currentProgress < 65) {
        addLog('ALINHANDO FASE COM O SINAL DE 40 µHz...');
      } else if (currentProgress >= 85 && currentProgress < 90) {
        addLog('EXTRAINDO ENTROPIA DA COORDENADA GEODÉSICA...');
      }

      if (currentProgress >= 100) {
        currentProgress = 100;
        clearInterval(interval);
        setIsDecoding(false);
        addLog('DECODIFICAÇÃO CONCLUÍDA COM SUCESSO.');
        
        // Generate a deterministic-looking mock private key based on the coordinates
        const mockKey = "0x" + Array.from({length: 64}, () => Math.floor(Math.random()*16).toString(16)).join('');
        setDecodedKey(mockKey);
        addLog(`CHAVE PRIVADA RECUPERADA: ${mockKey.substring(0, 10)}...${mockKey.substring(58)}`);
      }
      setProgress(currentProgress);
    }, 400);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="w-full max-w-3xl bg-arkhe-card border border-arkhe-cyan/30 rounded-xl shadow-[0_0_30px_rgba(0,255,170,0.1)] overflow-hidden flex flex-col">
        
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-arkhe-cyan/20 bg-arkhe-cyan/5">
          <div className="flex items-center gap-3">
            <Key className="w-6 h-6 text-arkhe-cyan" />
            <div>
              <h2 className="text-lg font-bold text-arkhe-cyan tracking-widest uppercase">Decodificador Geográfico</h2>
              <div className="text-xs font-mono text-arkhe-muted">Extração de Chave Privada via Anomalia Espacial</div>
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
                <Globe className="w-4 h-4" />
                Coordenadas Alvo
              </h3>
              <div className="space-y-2 font-mono text-sm">
                <div className="flex justify-between">
                  <span className="text-arkhe-muted">Latitude:</span>
                  <span className="text-arkhe-cyan">30.0444° N</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-arkhe-muted">Longitude:</span>
                  <span className="text-arkhe-cyan">31.2357° E</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-arkhe-muted">Localização:</span>
                  <span className="text-white">Cairo, Egito</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-arkhe-muted">Frequência Base:</span>
                  <span className="text-arkhe-purple">40.000 µHz</span>
                </div>
              </div>

              <button
                onClick={startDecoding}
                disabled={isDecoding || decodedKey !== null}
                className={`w-full py-3 mt-6 rounded font-mono text-sm uppercase tracking-widest transition-all ${
                  isDecoding 
                    ? 'bg-arkhe-cyan/20 text-arkhe-cyan border border-arkhe-cyan/50 cursor-not-allowed'
                    : decodedKey 
                      ? 'bg-arkhe-green/20 text-arkhe-green border border-arkhe-green/50 cursor-not-allowed'
                      : 'bg-arkhe-cyan/10 text-arkhe-cyan border border-arkhe-cyan hover:bg-arkhe-cyan/20 hover:shadow-[0_0_15px_rgba(0,255,170,0.3)]'
                }`}
              >
                {isDecoding ? (
                  <span className="flex items-center justify-center gap-2">
                    <Activity className="w-4 h-4 animate-spin" />
                    Decodificando...
                  </span>
                ) : decodedKey ? (
                  <span className="flex items-center justify-center gap-2">
                    <Unlock className="w-4 h-4" />
                    Chave Extraída
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    <Key className="w-4 h-4" />
                    Iniciar Decodificação
                  </span>
                )}
              </button>
            </div>

            {/* Progress */}
            <div className="bg-black/40 border border-arkhe-border p-4 rounded-lg">
               <div className="flex justify-between text-xs font-mono mb-2">
                <span className="text-arkhe-muted">Progresso da Extração</span>
                <span className="text-arkhe-cyan">{Math.round(progress)}%</span>
              </div>
              <div className="h-2 bg-arkhe-card rounded-full overflow-hidden border border-arkhe-border">
                <div 
                  className="h-full bg-arkhe-cyan transition-all duration-300 relative"
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
                <Database className="w-4 h-4" />
                Logs de Decodificação
              </h3>
              <div className="flex-1 overflow-y-auto font-mono text-xs space-y-1">
                {logs.map((log, i) => (
                  <div key={i} className={`${i === 0 ? 'text-arkhe-cyan' : 'text-arkhe-muted opacity-70'}`}>
                    {log}
                  </div>
                ))}
                {logs.length === 0 && (
                  <div className="text-arkhe-muted/50 italic">Aguardando inicialização...</div>
                )}
              </div>
            </div>

            {decodedKey && (
              <div className="bg-arkhe-green/10 border border-arkhe-green/30 p-4 rounded-lg animate-in fade-in slide-in-from-bottom-4">
                <h3 className="text-sm font-mono text-arkhe-green uppercase mb-2 flex items-center gap-2">
                  <Shield className="w-4 h-4" />
                  Chave Privada Recuperada
                </h3>
                <div className="bg-black/50 p-3 rounded border border-arkhe-green/20 font-mono text-xs text-arkhe-green break-all">
                  {decodedKey}
                </div>
                <p className="text-[10px] text-arkhe-green/70 mt-2 font-mono">
                  AVISO: Esta chave concede acesso ao nó de entropia mínima. Mantenha-a segura.
                </p>
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}
