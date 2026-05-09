
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Shield, Activity, Lock, Server, AlertTriangle, CheckCircle2, FileText } from 'lucide-react';
import React, { useState, useEffect } from 'react';

interface ArkheSecTelemetryPanelProps {
  onClose: () => void;
}

export default function ArkheSecTelemetryPanel({ onClose }: ArkheSecTelemetryPanelProps) {
  const [isMigrating, setIsMigrating] = useState(false);
  const [chainId, setChainId] = useState('2140 (Conflito: Oneness Network)');
  const [collectorStatus, setCollectorStatus] = useState('Sincronizando...');
  const [logs, setLogs] = useState<string[]>([]);
  const [redactionTestActive, setRedactionTestActive] = useState(false);

  const addLog = (msg: string) => {
    setLogs(prev => [`[${new Date().toISOString().split('T')[1].slice(0, 8)}] ${msg}`, ...prev].slice(0, 15));
  };

  useEffect(() => {
    addLog('INICIALIZANDO ARKHE-SEC v2140.2.0 (HARDENED PRODUCTION)...');
    addLog('VERIFICANDO mTLS COM PARSEABLE INGESTOR...');
    setTimeout(() => {
      addLog('mTLS ESTABELECIDO. OTLP COLLECTOR ONLINE.');
      setCollectorStatus('Online (mTLS Ativo)');
    }, 1500);
  }, []);

  const executeMigration = () => {
    setIsMigrating(true);
    addLog('INICIANDO MIGRAÇÃO DE CHAIN ID (ARKHE-GENESIS)...');
    addLog('ALVO: 0xCAFEBABE (3405691582)');

    setTimeout(() => {
      addLog('ATUALIZANDO RESOURCE ATTRIBUTES NO OTLP COLLECTOR...');
    }, 1000);

    setTimeout(() => {
      addLog('REINICIANDO PIPELINE DE LOGS...');
    }, 2500);

    setTimeout(() => {
      setChainId('3405691582 (0xCAFEBABE)');
      setIsMigrating(false);
      addLog('MIGRAÇÃO CONCLUÍDA. NOVO CHAIN ID ATIVO.');
    }, 4000);
  };

  const testRedaction = () => {
    setRedactionTestActive(true);
    addLog('INJETANDO LOG COM DADOS SENSÍVEIS (RAW)...');

    const rawLog = 'User authentication failed. IP: 192.168.1.45, Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c';

    setTimeout(() => {
      addLog(`RAW: ${rawLog.substring(0, 60)}...`);
    }, 500);

    setTimeout(() => {
      addLog('PROCESSADOR REDACTION ATUANDO...');
    }, 1500);

    setTimeout(() => {
      const redactedLog = rawLog
        .replace(/\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/g, '[REDACTED_IP]')
        .replace(/eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*/g, '[REDACTED_JWT]');
      addLog(`REDACTED: ${redactedLog}`);
      setRedactionTestActive(false);
    }, 2500);
  };

  const securityModules = [
    { name: 'Anti-DDoS Ativo', status: 'Operacional', lambda: 0.9992 },
    { name: 'WAAP (Web & API)', status: 'Operacional', lambda: 0.9985 },
    { name: 'Gestão de Vulnerabilidades', status: 'Varredura Concluída', lambda: 0.9910 },
    { name: 'Threat Intelligence (STIX/TAXII)', status: 'Sincronizado', lambda: 0.9850 },
    { name: 'SIEM (Markov Model)', status: 'Monitorando', lambda: 0.9990 },
    { name: 'Dark Web Exposure', status: 'Sem Alertas', lambda: 1.0000 },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="w-full max-w-5xl bg-arkhe-card border border-arkhe-green/30 rounded-xl shadow-[0_0_30px_rgba(0,255,102,0.1)] overflow-hidden flex flex-col max-h-[90vh]">

        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-arkhe-green/20 bg-arkhe-green/5">
          <div className="flex items-center gap-3">
            <Shield className="w-6 h-6 text-arkhe-green" />
            <div>
              <h2 className="text-lg font-bold text-arkhe-green tracking-widest uppercase">ARKHE-SEC Telemetria Coerente</h2>
              <div className="text-xs font-mono text-arkhe-muted">Parseable OTLP Pipeline v2.0 (Ω-Level 1)</div>
            </div>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            FECHAR [X]
          </button>
        </div>

        <div className="p-6 grid grid-cols-1 lg:grid-cols-3 gap-6 overflow-y-auto">

          {/* Status & Migration */}
          <div className="space-y-6 lg:col-span-1">
            <div className="bg-black/40 border border-arkhe-border p-4 rounded-lg">
              <h3 className="text-sm font-mono text-arkhe-muted uppercase mb-4 flex items-center gap-2">
                <Server className="w-4 h-4" />
                Status da Pipeline
              </h3>
              <div className="space-y-3 font-mono text-xs">
                <div className="flex justify-between items-center">
                  <span className="text-arkhe-muted">OTLP Collector:</span>
                  <span className={collectorStatus.includes('Online') ? 'text-arkhe-green' : 'text-arkhe-orange animate-pulse'}>
                    {collectorStatus}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-arkhe-muted">Parseable Ingestor:</span>
                  <span className="text-arkhe-green">Conectado</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-arkhe-muted">Buffering (File):</span>
                  <span className="text-arkhe-cyan">Ativo (0.01% uso)</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-arkhe-muted">Redaction:</span>
                  <span className="text-arkhe-purple">PII/JWT Bloqueados</span>
                </div>
              </div>
            </div>

            <div className="bg-black/40 border border-arkhe-border p-4 rounded-lg">
              <h3 className="text-sm font-mono text-arkhe-muted uppercase mb-4 flex items-center gap-2">
                <Lock className="w-4 h-4" />
                Governança Arkhe-Chain
              </h3>
              <div className="space-y-3 font-mono text-xs mb-4">
                <div className="flex flex-col gap-1">
                  <span className="text-arkhe-muted">Chain ID Atual:</span>
                  <span className={chainId.includes('Conflito') ? 'text-arkhe-red' : 'text-arkhe-green'}>
                    {chainId}
                  </span>
                </div>
              </div>

              <button
                onClick={executeMigration}
                disabled={isMigrating || !chainId.includes('Conflito')}
                className={`w-full py-3 rounded font-mono text-sm uppercase tracking-widest transition-all ${
                  isMigrating
                    ? 'bg-arkhe-orange/20 text-arkhe-orange border border-arkhe-orange/50 cursor-not-allowed'
                    : !chainId.includes('Conflito')
                      ? 'bg-arkhe-green/20 text-arkhe-green border border-arkhe-green/50 cursor-not-allowed'
                      : 'bg-arkhe-red/10 text-arkhe-red border border-arkhe-red hover:bg-arkhe-red/20 hover:shadow-[0_0_15px_rgba(255,51,102,0.3)]'
                }`}
              >
                {isMigrating ? (
                  <span className="flex items-center justify-center gap-2">
                    <Activity className="w-4 h-4 animate-spin" />
                    Migrando...
                  </span>
                ) : !chainId.includes('Conflito') ? (
                  <span className="flex items-center justify-center gap-2">
                    <CheckCircle2 className="w-4 h-4" />
                    Chain ID Atualizado
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    <AlertTriangle className="w-4 h-4" />
                    Migrar para 0xCAFEBABE
                  </span>
                )}
              </button>

              <button
                onClick={testRedaction}
                disabled={redactionTestActive}
                className={`w-full mt-4 py-3 rounded font-mono text-sm uppercase tracking-widest transition-all ${
                  redactionTestActive
                    ? 'bg-arkhe-purple/20 text-arkhe-purple border border-arkhe-purple/50 cursor-not-allowed'
                    : 'bg-arkhe-cyan/10 text-arkhe-cyan border border-arkhe-cyan hover:bg-arkhe-cyan/20 hover:shadow-[0_0_15px_rgba(0,255,170,0.3)]'
                }`}
              >
                {redactionTestActive ? (
                  <span className="flex items-center justify-center gap-2">
                    <Activity className="w-4 h-4 animate-spin" />
                    Redigindo Dados...
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    <Shield className="w-4 h-4" />
                    Testar Redaction Processor
                  </span>
                )}
              </button>
            </div>
          </div>

          {/* Security Modules */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-black/40 border border-arkhe-border p-4 rounded-lg">
               <h3 className="text-sm font-mono text-arkhe-muted uppercase mb-4 flex items-center gap-2">
                <Shield className="w-4 h-4" />
                Módulos de Segurança (Consórcio Archimedes)
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {securityModules.map((mod, i) => (
                  <div key={i} className="bg-arkhe-card border border-arkhe-border p-3 rounded flex flex-col gap-2">
                    <div className="flex justify-between items-start">
                      <span className="text-xs font-bold text-white">{mod.name}</span>
                      <span className="text-[10px] bg-arkhe-green/10 text-arkhe-green px-2 py-0.5 rounded border border-arkhe-green/20">
                        {mod.status}
                      </span>
                    </div>
                    <div className="flex justify-between items-center text-[10px] font-mono">
                      <span className="text-arkhe-muted">Coerência (λ₂):</span>
                      <span className="text-arkhe-cyan">{mod.lambda.toFixed(4)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Logs */}
            <div className="bg-black/60 border border-arkhe-border p-4 rounded-lg flex-1 flex flex-col min-h-[200px]">
              <h3 className="text-sm font-mono text-arkhe-muted uppercase mb-2 flex items-center gap-2">
                <FileText className="w-4 h-4" />
                Parseable Ingestion Logs
              </h3>
              <div className="flex-1 overflow-y-auto font-mono text-xs space-y-1">
                {logs.map((log, i) => (
                  <div key={i} className={`${i === 0 ? 'text-arkhe-green' : 'text-arkhe-muted opacity-70'}`}>
                    {log}
                  </div>
                ))}
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
