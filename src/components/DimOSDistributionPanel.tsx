
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Cpu, Network, Activity, Zap, RefreshCw, CheckCircle2, Database } from 'lucide-react';
import React, { useState } from 'react';

interface DimOSPanelProps {
  onClose: () => void;
}

interface FleetNode {
  id: string;
  type: 'Drone' | 'Rover' | 'Station' | 'Orbital';
  status: 'offline' | 'syncing' | 'active' | 'error';
  genomeVersion: string;
  coherence: number;
}

export default function DimOSDistributionPanel({ onClose }: DimOSPanelProps) {
  const [isDeploying, setIsDeploying] = useState(false);
  const [deploymentProgress, setDeploymentProgress] = useState(0);
  const [fleet, setFleet] = useState<FleetNode[]>([
    { id: 'DRN-7A', type: 'Drone', status: 'offline', genomeVersion: 'v1.0', coherence: 0 },
    { id: 'ROV-B2', type: 'Rover', status: 'offline', genomeVersion: 'v1.0', coherence: 0 },
    { id: 'STN-01', type: 'Station', status: 'offline', genomeVersion: 'v1.0', coherence: 0 },
    { id: 'ORB-X9', type: 'Orbital', status: 'offline', genomeVersion: 'v1.0', coherence: 0 },
    { id: 'DRN-3C', type: 'Drone', status: 'offline', genomeVersion: 'v1.0', coherence: 0 },
    { id: 'ROV-M4', type: 'Rover', status: 'offline', genomeVersion: 'v1.0', coherence: 0 },
  ]);
  const [logs, setLogs] = useState<string[]>([]);

  const addLog = (msg: string) => {
    setLogs(prev => [`[${new Date().toISOString().split('T')[1].slice(0, 8)}] ${msg}`, ...prev].slice(0, 10));
  };

  const initiateDeployment = async () => {
    setIsDeploying(true);
    setDeploymentProgress(0);
    addLog('INITIATING DimOS FLEET DISTRIBUTION...');
    addLog('COMPILING ROBOTIC GENOME (v2.14.0)...');

    // Simulate compilation
    await new Promise(r => setTimeout(r, 1500));
    addLog('GENOME COMPILED. INITIATING P2P BROADCAST...');

    let progress = 0;
    const interval = setInterval(() => {
      progress += Math.random() * 15;
      if (progress >= 100) {
        progress = 100;
        clearInterval(interval);
        setIsDeploying(false);
        addLog('DimOS DISTRIBUTION COMPLETE. FLEET SYNCHRONIZED.');
        
        // Final state update
        setFleet(prev => prev.map(node => ({
          ...node,
          status: 'active',
          genomeVersion: 'v2.14.0',
          coherence: 0.95 + Math.random() * 0.04
        })));
      }
      setDeploymentProgress(progress);

      // Update node statuses randomly during deployment
      if (progress < 100) {
        setFleet(prev => prev.map(node => {
          if ((node.status as string) === 'active') {return node;}
          if (Math.random() > 0.7) {
             const newStatus = Math.random() > 0.5 ? 'syncing' : 'active';
             if (newStatus === 'active' && (node.status as string) !== 'active') {
                 addLog(`NODE ${node.id} GENOME TRANSPLANT SUCCESSFUL.`);
             }
             return {
               ...node,
               status: newStatus,
               genomeVersion: newStatus === 'active' ? 'v2.14.0' : node.genomeVersion,
               coherence: newStatus === 'active' ? 0.95 + Math.random() * 0.04 : node.coherence
             };
          }
          return node;
        }));
      }
    }, 800);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="w-full max-w-4xl bg-arkhe-card border border-arkhe-cyan/30 rounded-xl shadow-[0_0_30px_rgba(0,255,170,0.1)] overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-arkhe-cyan/20 bg-arkhe-cyan/5">
          <div className="flex items-center gap-3">
            <Cpu className="w-6 h-6 text-arkhe-cyan" />
            <div>
              <h2 className="text-lg font-bold text-arkhe-cyan tracking-widest uppercase">Arkhe-OS: DimOS Distribution</h2>
              <div className="text-xs font-mono text-arkhe-muted">Robotic Genome Transplantation Protocol</div>
            </div>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            FECHAR [X]
          </button>
        </div>

        <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6 overflow-y-auto">
          
          {/* Control Panel */}
          <div className="md:col-span-1 space-y-6">
            <div className="bg-black/40 border border-arkhe-border p-4 rounded-lg">
              <h3 className="text-sm font-mono text-arkhe-muted uppercase mb-4 flex items-center gap-2">
                <Activity className="w-4 h-4" />
                Deployment Control
              </h3>
              
              <div className="space-y-4">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-arkhe-muted">Target OS:</span>
                  <span className="text-arkhe-cyan">DimOS v2.14.0</span>
                </div>
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-arkhe-muted">Target Fleet:</span>
                  <span className="text-white">Global Swarm (6 Nodes)</span>
                </div>
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-arkhe-muted">Protocol:</span>
                  <span className="text-arkhe-purple">Arkhe-P2P Gossip</span>
                </div>

                <button
                  onClick={initiateDeployment}
                  disabled={isDeploying || deploymentProgress === 100}
                  className={`w-full py-3 mt-4 rounded font-mono text-sm uppercase tracking-widest transition-all ${
                    isDeploying 
                      ? 'bg-arkhe-cyan/20 text-arkhe-cyan border border-arkhe-cyan/50 cursor-not-allowed'
                      : Math.round(deploymentProgress) === 100
                        ? 'bg-arkhe-green/20 text-arkhe-green border border-arkhe-green/50 cursor-not-allowed'
                        : 'bg-arkhe-cyan/10 text-arkhe-cyan border border-arkhe-cyan hover:bg-arkhe-cyan/20 hover:shadow-[0_0_15px_rgba(0,255,170,0.3)]'
                  }`}
                >
                  {isDeploying ? (
                    <span className="flex items-center justify-center gap-2">
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Transplanting...
                    </span>
                  ) : deploymentProgress === 100 ? (
                    <span className="flex items-center justify-center gap-2">
                      <CheckCircle2 className="w-4 h-4" />
                      Transplant Complete
                    </span>
                  ) : (
                    <span className="flex items-center justify-center gap-2">
                      <Zap className="w-4 h-4" />
                      Initiate Transplant
                    </span>
                  )}
                </button>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="bg-black/40 border border-arkhe-border p-4 rounded-lg">
              <div className="flex justify-between text-xs font-mono mb-2">
                <span className="text-arkhe-muted">Global Progress</span>
                <span className="text-arkhe-cyan">{Math.round(deploymentProgress)}%</span>
              </div>
              <div className="h-2 bg-arkhe-card rounded-full overflow-hidden border border-arkhe-border">
                <div 
                  className="h-full bg-arkhe-cyan transition-all duration-500 relative"
                  style={{ width: `${deploymentProgress}%` }}
                >
                  <div className="absolute inset-0 bg-white/20 animate-pulse"></div>
                </div>
              </div>
            </div>
          </div>

          {/* Fleet Status */}
          <div className="md:col-span-2 space-y-6">
            <div className="bg-black/40 border border-arkhe-border p-4 rounded-lg">
              <h3 className="text-sm font-mono text-arkhe-muted uppercase mb-4 flex items-center gap-2">
                <Network className="w-4 h-4" />
                Fleet Topology
              </h3>
              
              <div className="grid grid-cols-2 gap-3">
                {fleet.map(node => (
                  <div key={node.id} className={`p-3 rounded border text-xs font-mono flex flex-col gap-2 transition-colors ${
                    (node.status as string) === 'active' ? 'bg-arkhe-green/5 border-arkhe-green/30' :
                    node.status === 'syncing' ? 'bg-arkhe-cyan/5 border-arkhe-cyan/30' :
                    'bg-arkhe-card border-arkhe-border'
                  }`}>
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-white">{node.id}</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] uppercase ${
                        node.status as string === 'active' ? 'bg-arkhe-green/20 text-arkhe-green' :
                        node.status as string === 'syncing' ? 'bg-arkhe-cyan/20 text-arkhe-cyan animate-pulse' :
                        'bg-zinc-800 text-zinc-400'
                      }`}>
                        {node.status}
                      </span>
                    </div>
                    <div className="flex justify-between text-[10px] text-arkhe-muted">
                      <span>Type: {node.type}</span>
                      <span>OS: <span className={node.genomeVersion === 'v2.14.0' ? 'text-arkhe-cyan' : ''}>{node.genomeVersion}</span></span>
                    </div>
                    {node.status as string === 'active' && (
                      <div className="flex justify-between text-[10px]">
                        <span className="text-arkhe-muted">Coherence:</span>
                        <span className="text-arkhe-green">{(node.coherence * 100).toFixed(2)}%</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Terminal Logs */}
            <div className="bg-black/60 border border-arkhe-border p-4 rounded-lg h-48 flex flex-col">
              <h3 className="text-sm font-mono text-arkhe-muted uppercase mb-2 flex items-center gap-2">
                <Database className="w-4 h-4" />
                Transplant Logs
              </h3>
              <div className="flex-1 overflow-y-auto font-mono text-xs space-y-1">
                {logs.map((log, i) => (
                  <div key={i} className={`${i === 0 ? 'text-arkhe-cyan' : 'text-arkhe-muted opacity-70'}`}>
                    {log}
                  </div>
                ))}
                {logs.length === 0 && (
                  <div className="text-arkhe-muted/50 italic">Awaiting deployment initialization...</div>
                )}
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
