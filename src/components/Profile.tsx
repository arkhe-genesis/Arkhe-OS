
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { User, Shield, Activity, Key, Database, Cpu, Network } from 'lucide-react';
import React from 'react';
import { Link } from 'react-router-dom';

export default function Profile() {
  return (
    <div className="min-h-screen bg-arkhe-bg text-arkhe-text font-sans selection:bg-arkhe-cyan selection:text-black p-4 md:p-8">
      <header className="flex flex-col md:flex-row md:items-center justify-between mb-8 border-b border-arkhe-border pb-4 gap-4">
        <div className="flex items-center gap-4">
          <div className="relative">
            <User className="w-8 h-8 text-arkhe-cyan" />
            <div className="absolute inset-0 bg-arkhe-cyan blur-md opacity-20"></div>
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-widest uppercase">Arkhe-PNT <span className="text-arkhe-muted font-normal">// Operador</span></h1>
            <div className="flex items-center gap-2 text-xs font-mono mt-1">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-arkhe-green opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-arkhe-green"></span>
              </span>
              <span className="text-arkhe-green">IDENTIDADE VERIFICADA // NÍVEL Ω-1</span>
            </div>
          </div>
        </div>
        <nav className="flex gap-6 font-mono text-sm uppercase tracking-widest">
          <Link to="/dashboard" className="text-arkhe-muted hover:text-arkhe-cyan transition-colors">Dashboard</Link>
          <Link to="/profile" className="text-arkhe-cyan border-b border-arkhe-cyan pb-1">Profile</Link>
        </nav>
        <div className="flex items-center gap-6 font-mono text-xs text-arkhe-muted">
          <div className="flex flex-col items-end">
            <span className="uppercase tracking-wider">Sessão Ativa</span>
            <span className="text-arkhe-text">04:12:39</span>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Profile Card */}
        <div className="md:col-span-1 space-y-6">
          <div className="bg-arkhe-card border border-arkhe-border p-6 rounded-xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-arkhe-cyan/5 rounded-full blur-3xl"></div>
            <div className="flex flex-col items-center text-center">
              <div className="w-24 h-24 rounded-full border-2 border-arkhe-cyan/50 p-1 mb-4 relative">
                <div className="absolute inset-0 border border-arkhe-cyan rounded-full animate-[spin_10s_linear_infinite] border-t-transparent border-l-transparent"></div>
                <div className="w-full h-full bg-black rounded-full flex items-center justify-center overflow-hidden">
                  <User className="w-12 h-12 text-arkhe-cyan/70" />
                </div>
              </div>
              <h2 className="text-xl font-bold text-white uppercase tracking-widest">Operador 7G</h2>
              <div className="text-xs font-mono text-arkhe-muted mt-1">ID: ARK-9942-Ω</div>

              <div className="mt-6 w-full space-y-3">
                <div className="flex justify-between items-center text-sm font-mono border-b border-arkhe-border/50 pb-2">
                  <span className="text-arkhe-muted">Clearance</span>
                  <span className="text-arkhe-cyan font-bold">Nível Ω-1</span>
                </div>
                <div className="flex justify-between items-center text-sm font-mono border-b border-arkhe-border/50 pb-2">
                  <span className="text-arkhe-muted">Coerência Pessoal</span>
                  <span className="text-arkhe-green">λ₂ = 0.9994</span>
                </div>
                <div className="flex justify-between items-center text-sm font-mono border-b border-arkhe-border/50 pb-2">
                  <span className="text-arkhe-muted">Status Neural</span>
                  <span className="text-arkhe-cyan">Sincronizado</span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-arkhe-card border border-arkhe-border p-6 rounded-xl">
            <h3 className="text-sm font-mono text-arkhe-muted uppercase mb-4 flex items-center gap-2">
              <Key className="w-4 h-4" />
              Credenciais Criptográficas
            </h3>
            <div className="space-y-4">
              <div>
                <div className="text-xs text-arkhe-muted mb-1">Chave Pública (Arkhe-Chain)</div>
                <div className="font-mono text-[10px] text-arkhe-cyan bg-black/50 p-2 rounded break-all border border-arkhe-cyan/20">
                  0x7F4A...9B2E (Derivada da CPG Giza)
                </div>
              </div>
              <div>
                <div className="text-xs text-arkhe-muted mb-1">Assinatura Quântica</div>
                <div className="font-mono text-[10px] text-arkhe-purple bg-black/50 p-2 rounded break-all border border-arkhe-purple/20">
                  Q-SIG-9942-ALPHA-OMEGA-7731
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Activity & Stats */}
        <div className="md:col-span-2 space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-arkhe-card border border-arkhe-border p-4 rounded-xl flex items-center gap-4">
              <div className="p-3 bg-arkhe-cyan/10 rounded-lg">
                <Activity className="w-6 h-6 text-arkhe-cyan" />
              </div>
              <div>
                <div className="text-xs font-mono text-arkhe-muted uppercase">Intervenções</div>
                <div className="text-2xl font-bold text-white">1,042</div>
              </div>
            </div>
            <div className="bg-arkhe-card border border-arkhe-border p-4 rounded-xl flex items-center gap-4">
              <div className="p-3 bg-arkhe-purple/10 rounded-lg">
                <Shield className="w-6 h-6 text-arkhe-purple" />
              </div>
              <div>
                <div className="text-xs font-mono text-arkhe-muted uppercase">Ameaças Mitigadas</div>
                <div className="text-2xl font-bold text-white">847</div>
              </div>
            </div>
            <div className="bg-arkhe-card border border-arkhe-border p-4 rounded-xl flex items-center gap-4">
              <div className="p-3 bg-blue-500/10 rounded-lg">
                <Database className="w-6 h-6 text-blue-500" />
              </div>
              <div>
                <div className="text-xs font-mono text-arkhe-muted uppercase">Blocos Assinados</div>
                <div className="text-2xl font-bold text-white">128</div>
              </div>
            </div>
            <div className="bg-arkhe-card border border-arkhe-border p-4 rounded-xl flex items-center gap-4">
              <div className="p-3 bg-arkhe-green/10 rounded-lg">
                <Network className="w-6 h-6 text-arkhe-green" />
              </div>
              <div>
                <div className="text-xs font-mono text-arkhe-muted uppercase">Nós Sincronizados</div>
                <div className="text-2xl font-bold text-white">14/14</div>
              </div>
            </div>
          </div>

          <div className="bg-arkhe-card border border-arkhe-border p-6 rounded-xl">
            <h3 className="text-sm font-mono text-arkhe-muted uppercase mb-4 flex items-center gap-2">
              <Cpu className="w-4 h-4" />
              Histórico de Operações Recentes
            </h3>
            <div className="space-y-3">
              {[
                { action: 'Sincronização de Bio-Nó', target: 'Setor 7G', time: '10 min atrás', status: 'success' },
                { action: 'Assinatura Bloco Gênese', target: 'Arkhe-Chain (2147483647)', time: '2 horas atrás', status: 'success' },
                { action: 'Varredura de Anomalia', target: 'Triângulo das Bermudas', time: '5 horas atrás', status: 'success' },
                { action: 'Mitigação de Ameaça', target: 'Ataque DDoS (Camada 7)', time: '1 dia atrás', status: 'warning' },
                { action: 'Calibração Kuramoto', target: 'QPU Principal', time: '2 dias atrás', status: 'success' },
              ].map((log, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-black/40 border border-arkhe-border/50 rounded">
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${log.status === 'success' ? 'bg-arkhe-green' : 'bg-arkhe-orange'}`}></div>
                    <div>
                      <div className="text-sm font-bold text-white">{log.action}</div>
                      <div className="text-xs font-mono text-arkhe-muted">{log.target}</div>
                    </div>
                  </div>
                  <div className="text-xs font-mono text-arkhe-muted">{log.time}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
