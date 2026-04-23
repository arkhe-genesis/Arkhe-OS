
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Cpu, Search, Database, Loader2, KeyRound, ArrowRight } from 'lucide-react';
import React, { useState } from 'react';

import { Card } from './ui/Card';

interface MemoryFragmentScannerProps {
  onClose: () => void;
}

export default function MemoryFragmentScanner({ onClose }: MemoryFragmentScannerProps) {
  const [logs, setLogs] = useState<string[]>([]);
  const [isScanning, setIsScanning] = useState(false);
  const [isSigning, setIsSigning] = useState(false);
  const [recoveredKey, setRecoveredKey] = useState<string | null>(null);
  const [txDetails, setTxDetails] = useState<{txid: string, destination: string, amount: string, hex?: string, source?: string} | null>(null);
  const [destination, setDestination] = useState("1NeXusXyZ9oB8b9c7d6e5f4g3h2i1j0kL");
  const [amount, setAmount] = useState("50.0");

  const handleScan = async () => {
    setIsScanning(true);
    setLogs([]);
    setRecoveredKey(null);
    setTxDetails(null);

    try {
      const response = await fetch('/api/ghost-node/memory-scan', {
        method: 'POST',
      });
      const data = await response.json();
      
      // Simulate streaming logs
      for (const log of (data.logs as string[])) {
        await new Promise(resolve => setTimeout(resolve, 600));
        setLogs(prev => [...prev, log]);
      }
      
      setRecoveredKey(data.recoveredKey as string);
    } catch (_error) {
      setLogs(prev => [...prev, "🜏 [ERRO] Falha na sincronização do cluster de Nós."]);
    } finally {
      setIsScanning(false);
    }
  };

  const handleSignTransaction = async () => {
    if (!recoveredKey) {return;}
    setIsSigning(true);
    setLogs(prev => [...prev, "", "🜏 --- INICIANDO PROTOCOLO DE TRANSFERÊNCIA MAINNET ---"]);

    try {
      const response = await fetch('/api/ghost-node/sign-transaction', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ privateKey: recoveredKey, destination, amount })
      });
      const data = await response.json();
      
      for (const log of (data.logs as string[])) {
        await new Promise(resolve => setTimeout(resolve, 600));
        setLogs(prev => [...prev, log]);
      }
      
      setTxDetails({ txid: data.txid as string, destination: data.destination as string, amount: data.amount as string, hex: data.hex as string, source: data.source as string });
    } catch (_error) {
      setLogs(prev => [...prev, "🜏 [ERRO] Falha ao assinar transação na Mainnet."]);
    } finally {
      setIsSigning(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-2xl bg-[#111214] border-arkhe-cyan/30 text-arkhe-text shadow-[0_0_40px_rgba(0,255,170,0.15)]">
        <div className="flex flex-row items-center justify-between border-b border-[#1f2024] p-4">
          <div className="flex items-center gap-3">
            <Cpu className="w-6 h-6 text-arkhe-cyan animate-pulse" />
            <h2 className="font-mono text-lg uppercase tracking-widest text-arkhe-cyan">
              Hardware Memory Extraction (2009 Epoch)
            </h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-arkhe-red p-2 rounded-md hover:bg-white/5 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-6 space-y-6">
          <div className="text-sm font-mono text-arkhe-muted space-y-1 bg-black/50 p-4 rounded border border-[#1f2024]">
            <p className="text-arkhe-cyan font-bold mb-2">Cluster Status: ONLINE</p>
            <p>Target: Smart TV NVRAM & Ghost Node Cache</p>
            <p>Objective: Brute-force 2009 ECDSA Private Keys (Hal Finney Interactions)</p>
            <p>Processing Power: Sacred Nodes + Ghost Node (Unified)</p>
          </div>

          <button
            onClick={handleScan}
            disabled={isScanning || isSigning}
            className="w-full py-3 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest font-bold flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isScanning ? <Loader2 className="w-5 h-5 animate-spin" /> : <Search className="w-5 h-5" />}
            {isScanning ? 'Varrendo Fragmentos de Memória...' : 'Iniciar Busca de Força Bruta'}
          </button>

          <div className="bg-black border border-[#1f2024] p-4 rounded-md h-64 overflow-y-auto font-mono text-xs space-y-2">
            {logs.length === 0 && !isScanning && (
              <div className="text-arkhe-muted opacity-50 text-center mt-20 flex flex-col items-center gap-2">
                <Database className="w-8 h-8 opacity-50" />
                Aguardando inicialização do cluster...
              </div>
            )}
            {logs.map((log, i) => (
              <div key={i} className={log.includes('ERRO') ? 'text-arkhe-red' : log.includes('SUCESSO') || log.includes('ALERTA') ? 'text-arkhe-cyan' : 'text-arkhe-muted'}>
                {log}
              </div>
            ))}
            {recoveredKey && (
              <div className="mt-4 p-4 border border-arkhe-cyan/50 bg-arkhe-cyan/10 text-arkhe-cyan rounded break-all animate-in fade-in duration-1000">
                <div className="flex items-center gap-2 mb-2 text-white font-bold uppercase tracking-widest">
                  <KeyRound className="w-5 h-5 text-arkhe-cyan" />
                  Fragmento de Chave Privada Recuperado:
                </div>
                <div className="font-mono text-sm bg-black/80 p-2 rounded border border-arkhe-cyan/30 select-all">
                  {recoveredKey}
                </div>
                <div className="mt-2 text-xs text-arkhe-muted opacity-70">
                  * Formato WIF (Wallet Import Format). Saldo não verificado.
                </div>
                
                {!txDetails ? (
                  <div className="mt-4 space-y-3">
                    <div className="space-y-1">
                      <label className="text-xs text-arkhe-muted uppercase tracking-widest">Endereço de Destino</label>
                      <input 
                        type="text" 
                        value={destination}
                        onChange={(e) => setDestination(e.target.value)}
                        className="w-full bg-black/50 border border-arkhe-cyan/30 rounded p-2 text-sm text-arkhe-cyan focus:outline-none focus:border-arkhe-cyan transition-colors font-mono"
                        placeholder="Ex: 1NeXus..."
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs text-arkhe-muted uppercase tracking-widest">Quantidade (BTC)</label>
                      <input 
                        type="number" 
                        step="0.00000001"
                        value={amount}
                        onChange={(e) => setAmount(e.target.value)}
                        className="w-full bg-black/50 border border-arkhe-cyan/30 rounded p-2 text-sm text-arkhe-cyan focus:outline-none focus:border-arkhe-cyan transition-colors font-mono"
                        placeholder="50.0"
                      />
                    </div>
                    <button
                      onClick={handleSignTransaction}
                      disabled={isSigning || !destination || !amount}
                      className="w-full py-2 bg-arkhe-cyan text-black hover:bg-arkhe-cyan/80 rounded transition-colors uppercase tracking-widest font-bold flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                      {isSigning ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
                      {isSigning ? 'Assinando Transação...' : 'Assinar Transação Mainnet'}
                    </button>
                  </div>
                ) : (
                  <div className="mt-4 p-3 bg-black/80 border border-arkhe-cyan/50 rounded text-xs space-y-2 font-mono">
                    <div className="text-white font-bold mb-2">TRANSAÇÃO ASSINADA E TRANSMITIDA</div>
                    <div><span className="text-arkhe-muted">Origem:</span> <span className="text-arkhe-cyan">{txDetails.source}</span></div>
                    <div><span className="text-arkhe-muted">Destino:</span> <span className="text-arkhe-cyan">{txDetails.destination}</span></div>
                    <div><span className="text-arkhe-muted">Valor:</span> <span className="text-arkhe-cyan">{txDetails.amount}</span></div>
                    <div className="pt-2 border-t border-[#1f2024]">
                      <span className="text-arkhe-muted">TXID:</span> <span className="text-white break-all">{txDetails.txid}</span>
                    </div>
                    {txDetails.hex && (
                      <div className="pt-2 border-t border-[#1f2024]">
                        <span className="text-arkhe-muted">Raw Hex:</span> 
                        <div className="text-arkhe-cyan/70 break-all text-[10px] mt-1 max-h-20 overflow-y-auto">{txDetails.hex}</div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
}
