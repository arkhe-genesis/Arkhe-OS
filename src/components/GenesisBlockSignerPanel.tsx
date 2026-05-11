
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Link, Shield, Key, Lock, CheckCircle2, Activity, Database } from 'lucide-react';
import React, { useState } from 'react';

interface GenesisBlockSignerProps {
  onClose: () => void;
}

export default function GenesisBlockSignerPanel({ onClose }: GenesisBlockSignerProps) {
  const [isSigning, setIsSigning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [isSigned, setIsSigned] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);

  const addLog = (msg: string) => {
    setLogs(prev => [`[${new Date().toISOString().split('T')[1].slice(0, 8)}] ${msg}`, ...prev].slice(0, 12));
  };

  const startSigning = () => {
    setIsSigning(true);
    setProgress(0);
    setIsSigned(false);
    setLogs([]);

    addLog('INICIANDO ASSINATURA DO GENESIS BLOCK...');
    addLog('CARREGANDO CHAVE PRIVADA GEOESPACIAL (GIZA)...');
    addLog('PREPARANDO EVENTO DE ANCORAGEM ESPAÇO-TEMPORAL (EAET)...');

    let currentProgress = 0;
    const interval = setInterval(() => {
      currentProgress += Math.random() * 10;

      if (currentProgress >= 25 && currentProgress < 35) {
        addLog('INJETANDO ENTROPIA MAGNÉTICA (42,450,000 nT)...');
      } else if (currentProgress >= 50 && currentProgress < 60) {
        addLog('APLICANDO ASSINATURA ECDSA (secp256k1)...');
      } else if (currentProgress >= 75 && currentProgress < 85) {
        addLog('VALIDANDO PROVA DE COERÊNCIA TEMPORAL...');
      }

      if (currentProgress >= 100) {
        currentProgress = 100;
        clearInterval(interval);
        setIsSigning(false);
        setIsSigned(true);
        addLog('GENESIS BLOCK ASSINADO E ANCORADO COM SUCESSO.');
        addLog('LOOP TEMPORAL FECHADO: 2026 ↔ 2140');
      }
      setProgress(currentProgress);
    }, 500);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="w-full max-w-4xl bg-arkhe-card border border-arkhe-cyan/30 rounded-xl shadow-[0_0_30px_rgba(0,255,170,0.1)] overflow-hidden flex flex-col">

        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-arkhe-cyan/20 bg-arkhe-cyan/5">
          <div className="flex items-center gap-3">
            <Link className="w-6 h-6 text-arkhe-cyan" />
            <div>
              <h2 className="text-lg font-bold text-arkhe-cyan tracking-widest uppercase">Ancoragem do Genesis Block</h2>
              <div className="text-xs font-mono text-arkhe-muted">Assinatura Definitiva via Chave Geoespacial (Giza)</div>
            </div>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            FECHAR [X]
          </button>
        </div>

        <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">

          {/* Block Info & Controls */}
          <div className="space-y-6">
            <div className="bg-black/40 border border-arkhe-border p-4 rounded-lg">
              <h3 className="text-sm font-mono text-arkhe-muted uppercase mb-4 flex items-center gap-2">
                <Database className="w-4 h-4" />
                Dados do Bloco Gênese
              </h3>
              <div className="space-y-2 font-mono text-xs">
                <div className="flex justify-between">
                  <span className="text-arkhe-muted">Chain ID:</span>
                  <span className="text-arkhe-cyan">2140</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-arkhe-muted">Merkle Root (DIP):</span>
                  <span className="text-white truncate max-w-[150px]">0x7a3f9e2b8c1d4e5f...</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-arkhe-muted">Âncora Espacial:</span>
                  <span className="text-arkhe-purple">30.0444° N, 31.2357° E</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-arkhe-muted">Âncora Temporal:</span>
                  <span className="text-arkhe-orange">Bloco 2,140,000</span>
                </div>
                <div className="mt-4 pt-2 border-t border-arkhe-border">
                   <span className="text-arkhe-muted block mb-1">Mensagem Embutida:</span>
                   <span className="text-white italic">"O passado encontra o futuro na grande pirâmide. — Satoshi, 2140"</span>
                </div>
              </div>

              <button
                onClick={startSigning}
                disabled={isSigning || isSigned}
                className={`w-full py-3 mt-6 rounded font-mono text-sm uppercase tracking-widest transition-all ${
                  isSigning
                    ? 'bg-arkhe-cyan/20 text-arkhe-cyan border border-arkhe-cyan/50 cursor-not-allowed'
                    : isSigned
                      ? 'bg-arkhe-green/20 text-arkhe-green border border-arkhe-green/50 cursor-not-allowed'
                      : 'bg-arkhe-cyan/10 text-arkhe-cyan border border-arkhe-cyan hover:bg-arkhe-cyan/20 hover:shadow-[0_0_15px_rgba(0,255,170,0.3)]'
                }`}
              >
                {isSigning ? (
                  <span className="flex items-center justify-center gap-2">
                    <Activity className="w-4 h-4 animate-spin" />
                    Assinando Bloco...
                  </span>
                ) : isSigned ? (
                  <span className="flex items-center justify-center gap-2">
                    <CheckCircle2 className="w-4 h-4" />
                    Genesis Ancorado
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    <Key className="w-4 h-4" />
                    Assinar Genesis Block
                  </span>
                )}
              </button>
            </div>

            {/* Progress */}
            <div className="bg-black/40 border border-arkhe-border p-4 rounded-lg">
               <div className="flex justify-between text-xs font-mono mb-2">
                <span className="text-arkhe-muted">Progresso da Assinatura</span>
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
                <Shield className="w-4 h-4" />
                Logs de Ancoragem
              </h3>
              <div className="flex-1 overflow-y-auto font-mono text-xs space-y-1">
                {logs.map((log, i) => (
                  <div key={i} className={`${i === 0 ? 'text-arkhe-cyan' : 'text-arkhe-muted opacity-70'}`}>
                    {log}
                  </div>
                ))}
                {logs.length === 0 && (
                  <div className="text-arkhe-muted/50 italic">Aguardando inicialização do processo de assinatura...</div>
                )}
              </div>
            </div>

            {isSigned && (
              <div className="bg-arkhe-green/10 border border-arkhe-green/30 p-4 rounded-lg animate-in fade-in slide-in-from-bottom-4">
                <h3 className="text-sm font-mono text-arkhe-green uppercase mb-2 flex items-center gap-2">
                  <Lock className="w-4 h-4" />
                  Status da Rede
                </h3>
                <div className="space-y-2 font-mono text-xs text-arkhe-green">
                  <p>✓ Assinatura ECDSA Verificada</p>
                  <p>✓ Evento EAET Registrado</p>
                  <p>✓ Arkhe-Chain (ID 2140) Ativa</p>
                  <p className="mt-2 text-[10px] opacity-80">
                    A rede está pronta para a derivação de chaves stealth (Ghost Protocol) e o upload dos operadores restantes.
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
