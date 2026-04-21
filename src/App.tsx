/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Shield, Settings, Menu, Bell, Search, Info, Terminal, Video, Smartphone, Hammer, TrendingUp } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import React, { useState } from 'react';

import AquiferSpectrogramPanel from './components/AquiferSpectrogramPanel';
import ArkheCliPanel from './components/ArkheCliPanel';
import ArkheGridSimulator from './components/ArkheGridSimulator';
import ForgeStudioPanel from './components/ForgeStudioPanel';
import ArkheTVPanel from './components/ArkheTVPanel';
import BonsaiPrismPanel from './components/BonsaiPrismPanel';
import CHSHMonitorPanel from './components/CHSHMonitorPanel';
import CoherenceMonitor from './components/CoherenceMonitor';
import CommandCenter from './components/CommandCenter';
import ConsensusMeter from './components/ConsensusMeter';
import CorvoNoirDashboard from './components/CorvoNoirDashboard';
import DataCoherenceDashboard from './components/DataCoherenceDashboard';
import EnterprisePlusPanel from './components/EnterprisePlusPanel';
import GeoKeyDecoderPanel from './components/GeoKeyDecoderPanel';
import IntelligenceHub from './components/IntelligenceHub';
import ManifestationCycle from './components/ManifestationCycle';
import MitigationEngine from './components/MitigationEngine';
import MolecularCommunicationPanel from './components/MolecularCommunicationPanel';
import NekoPanel from './components/NekoPanel';
import NetworkStatus from './components/NetworkStatus';
import OrbitalComputePanel from './components/OrbitalComputePanel';
import PolyglotCompilerPanel from './components/PolyglotCompilerPanel';
import ProofOfIntelligencePanel from './components/ProofOfIntelligencePanel';
import QubitPipelinePanel from './components/QubitPipelinePanel';
import RamseyConfirmationModal from './components/RamseyConfirmationModal';
import ResearchAgentsPanel from './components/ResearchAgentsPanel';
import SessionReplayViewer from './components/SessionReplayViewer';
import SpectraYieldPanel from './components/SpectraYieldPanel';
import TemporalLensPanel from './components/TemporalLensPanel';
import TemporalLog from './components/TemporalLog';
import TemporalStreamViewer from './components/TemporalStreamViewer';
import ArkheOntologyVision from './components/ArkheOntologyVision';
import ChipFabricationVision from './components/ChipFabricationVision';
import ThreatDetection from './components/ThreatDetection';
import ThukdamProtocolPanel from './components/ThukdamProtocolPanel';
import TimechainVisualizer from './components/TimechainVisualizer';
import TzinorNetworkPanel from './components/TzinorNetworkPanel';
import TzinorTerminal from './components/TzinorTerminal';
import UnifiedOntologyPanel from './components/UnifiedOntologyPanel';
import VideoGenerationPanel from './components/VideoGenerationPanel';
import X402WalletPanel from './components/X402WalletPanel';
import YangBaxterVerifier from './components/YangBaxterVerifier';
import ZkERCSimulator from './components/ZkERCSimulator';
import { useArkheSimulation } from './hooks/useArkheSimulation';

export default function App() {
  const state = useArkheSimulation();
  const [activePanel, setActivePanel] = useState<'simulation' | 'command' | 'intelligence' | 'network' | 'governance' | 'corvo' | 'enterprise' | 'bonsai' | 'neko' | 'dashboard' | 'forge' | 'spectra'>('simulation');
  const [showTzinor, setShowTzinor] = useState(false);
  const [showTelevision, setShowTelevision] = useState(false);
  const [showVideoGen, setShowVideoGen] = useState(false);
  const [showTemporalStream, setShowTemporalStream] = useState(false);
  const [showArkheOntologyVision, setShowArkheOntologyVision] = useState(false);
  const [showChipFabricationVision, setShowChipFabricationVision] = useState(false);

  const navigation = [
    { id: 'simulation', label: 'Reality Simulation', icon: Shield },
    { id: 'dashboard', label: 'Data Coherence', icon: Bell },
    { id: 'command', label: 'Command Center', icon: Menu },
    { id: 'intelligence', label: 'Bio-Quantum Intel', icon: Info },
    { id: 'network', label: 'Starlink-Ω Fabric', icon: Settings },
    { id: 'corvo', label: 'Corvo Noir OS', icon: Shield },
    { id: 'enterprise', label: 'Enterprise Plus', icon: Shield },
    { id: 'bonsai', label: 'Bonsai Prism', icon: Shield },
    { id: 'neko', label: 'Neko Browser', icon: Shield },
    { id: 'forge', label: 'A-Forge Studio', icon: Hammer },
    { id: 'spectra', label: 'Spectra Yield', icon: TrendingUp },
  ];

  return (
    <div className="min-h-screen bg-[#020305] text-arkhe-text selection:bg-arkhe-cyan/30 selection:text-arkhe-cyan">
      {/* Navigation Header */}
      <header className="border-b border-arkhe-border/50 bg-black/40 backdrop-blur-xl sticky top-0 z-40">
        <div className="max-w-[1800px] mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-arkhe-cyan rounded-lg flex items-center justify-center shadow-[0_0_20px_rgba(0,229,255,0.4)]">
                <Shield className="w-5 h-5 text-black" />
              </div>
              <h1 className="font-mono text-xl font-bold tracking-tighter uppercase">
                Arkhe<span className="text-arkhe-cyan">(n)</span>
                <span className="ml-2 text-[10px] text-arkhe-muted border border-arkhe-border px-1.5 py-0.5 rounded tracking-widest">V1.4-Ω</span>
              </h1>
            </div>

            <nav className="hidden lg:flex items-center gap-1">
              {navigation.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setActivePanel(item.id as any)}
                  className={`px-4 py-2 rounded-md font-mono text-xs uppercase tracking-wider transition-all flex items-center gap-2 ${
                    activePanel === item.id
                      ? 'bg-arkhe-cyan/10 text-arkhe-cyan border border-arkhe-cyan/30 shadow-[0_0_15px_rgba(0,229,255,0.1)]'
                      : 'text-arkhe-muted hover:text-white'
                  }`}
                >
                  <item.icon className="w-3.5 h-3.5" />
                  {item.label}
                </button>
              ))}
            </nav>
          </div>

          <div className="flex items-center gap-4">
            <button
               onClick={() => setShowTelevision(true)}
               className="p-2 text-arkhe-muted hover:text-arkhe-cyan transition-colors"
               title="Arkhe TV"
            >
              <Video className="w-5 h-5" />
            </button>
            <button
               onClick={() => setShowTemporalStream(true)}
               className="p-2 text-arkhe-muted hover:text-cyan-400 transition-colors"
               title="Temporal Stream Viewer"
            >
              <Terminal className="w-5 h-5 text-cyan-500" />
            </button>
            <button 
              onClick={() => setShowVideoGen(true)}
              className="px-3 py-1.5 bg-arkhe-cyan/10 border border-arkhe-cyan/50 text-arkhe-cyan rounded font-mono text-[10px] uppercase hover:bg-arkhe-cyan/20 transition-all flex items-center gap-2"
            >
               <Video className="w-3 h-3" />
               Project Intent
            </button>
            <button
              onClick={() => setShowTzinor(!showTzinor)}
              className={`p-2 rounded-md transition-all ${showTzinor ? 'bg-arkhe-orange/20 text-arkhe-orange border border-arkhe-orange/50' : 'text-arkhe-muted hover:text-arkhe-orange hover:bg-arkhe-orange/5'}`}
            >
              <Terminal className="w-5 h-5" />
            </button>
            <div className="h-6 w-px bg-arkhe-border/50 mx-2" />
            <div className="flex flex-col items-end">
              <div className="text-[10px] font-mono text-arkhe-muted uppercase">Global Phase</div>
              <div className="text-xs font-mono font-bold text-arkhe-cyan animate-pulse">
                {(state.edge.phase || 0).toFixed(4)} rad
              </div>
            </div>
            <div className="flex flex-col items-end ml-4">
              <div className="text-[10px] font-mono text-arkhe-muted uppercase tracking-tighter">System Health</div>
              <div className="text-lg font-bold uppercase tracking-widest leading-none">
                {state.security.zkProofValid ? 'Verified' : 'Compromised'}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-[1800px] mx-auto p-6 min-h-[calc(100vh-4rem)]">
        <AnimatePresence mode="wait">
          {activePanel === 'simulation' && (
            <motion.div
              key="simulation"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="grid grid-cols-1 lg:grid-cols-3 xl:grid-cols-4 gap-6"
            >
              <div className="lg:col-span-2 xl:col-span-2 space-y-6 flex flex-col">
                <CoherenceMonitor data={state.coherenceData} currentLambda={state.currentLambda} />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <TzinorNetworkPanel network={state.tzinorNetwork as any} />
                  <ManifestationCycle manifestation={state.manifestation} />
                </div>
                <div className="h-[280px]">
                  <TzinorTerminal tzinor={state.tzinor as any} threatLevel={state.threatLevel} />
                </div>
                <TimechainVisualizer logs={state.logs} />
                <div className="flex-1 min-h-[300px]">
                  <TemporalLog logs={state.logs} />
                </div>
              </div>
              <div className="space-y-6 flex flex-col">
                <X402WalletPanel wallet={state.x402Wallet as any} />
                <ThreatDetection metrics={state.metrics} metricsHistory={state.metricsHistory} threatLevel={state.threatLevel} />
                <OrbitalComputePanel orbital={state.orbital} />
                <MitigationEngine mitigation={state.mitigation} hardware={state.hardware} activeThreat={state.activeThreat} />
                <ArkheGridSimulator onClose={() => setActivePanel("simulation")} />
              </div>
            </motion.div>
          )}

          {activePanel === 'dashboard' && (
            <motion.div key="dashboard" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <DataCoherenceDashboard onClose={() => setActivePanel("simulation")} />
            </motion.div>
          )}

          {activePanel === 'command' && (
            <motion.div key="command" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <CommandCenter
                attackType="none"
                setAttackType={() => {}}
                attackTypes={[]}
                setPiDayText={() => {}}
                setShowPodmanTerminal={() => {}}
                setShowCoherenceField={() => {}}
                setShowHybridArch={() => {}}
                setShowOuroboros={() => {}}
                setShowBioNodes={() => {}}
                setShowMolecular={() => {}}
                setShowNeuralBridge={() => {}}
                setShowRNA={() => {}}
                setShowOrbes={() => {}}
                setShowThukdam={() => {}}
                setShowMultiversal={() => {}}
                setShowConsciousness={() => {}}
                setShowShaka={() => {}}
                setShowGoogleBridge={() => {}}
                setShowTimechain={() => {}}
                setShowArkheTV={() => {}}
                setShowPolyglot={() => {}}
                setShowCluster={() => {}}
                setShowArkheGrid={() => {}}
                setShowZkERC={() => {}}
                setShowIntelligencePanel={() => {}}
                setShowIntelligenceHub={() => {}}
                setShowOrchestrationLayer={() => {}}
                setShowAIP005={() => {}}
                setShowResearchAgents={() => {}}
                setShowSepoliaIntegration={() => {}}
                setShowArkheCli={() => {}}
                setShowP2PNetwork={() => {}}
                setShowVideoGeneration={() => {}}
                setShowPhaseSteg={() => {}}
                setShowDysonSphere={() => {}}
                setShowDimOS={() => {}}
                setShowGeoKey={() => {}}
                setShowGenesisBlock={() => {}}
                setShowGhostProtocol={() => {}}
                setShowArkheSec={() => {}}
                setShowBermudaAnomaly={() => {}}
                setShowCollectiveIntelligence={() => {}}
                setShowArkheVision={() => {}}
                setShowAgentManagement={() => {}}
                setShowAquiferSpectrogram={() => {}}
                setShowUnifiedOntology={() => {}}
                setShowArkheOntologyVision={() => setShowArkheOntologyVision(true)}
                setShowChipFabricationVision={() => setShowChipFabricationVision(true)}
                setShowSecurityAdvanced={() => {}}
                setShowPluralityMCP={() => {}}
                setShowVelxioEmulation={() => {}}
                setShowSpectra={() => setActivePanel('spectra')}
                parameters={state.parameters}
              />
            </motion.div>
          )}

          {activePanel === 'intelligence' && (
            <motion.div key="intelligence" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="grid grid-cols-1 md:grid-cols-2 gap-6">
               <IntelligenceHub onClose={() => setActivePanel("simulation")} />
               <ProofOfIntelligencePanel onClose={() => setActivePanel("simulation")} />
               <div className="md:col-span-2">
                 <UnifiedOntologyPanel onClose={() => {}} />
               </div>
            </motion.div>
          )}

          {activePanel === 'network' && (
             <motion.div key="network" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-6">
               <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <NetworkStatus shards={state.shards} />
                  <MolecularCommunicationPanel onClose={() => setActivePanel("simulation")} />
               </div>
               <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                 <QubitPipelinePanel onClose={() => setActivePanel("simulation")} />
                 <CHSHMonitorPanel onClose={() => setActivePanel("simulation")} />
                 <YangBaxterVerifier topology={state.topology} security={state.security} />
               </div>
             </motion.div>
          )}

          {activePanel === 'corvo' && (
            <motion.div key="corvo" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <CorvoNoirDashboard />
            </motion.div>
          )}

          {activePanel === 'enterprise' && (
            <motion.div key="enterprise" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <EnterprisePlusPanel onClose={() => setActivePanel("simulation")} />
            </motion.div>
          )}

          {activePanel === 'bonsai' && (
            <motion.div key="bonsai" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <BonsaiPrismPanel onClose={() => setActivePanel('simulation')} />
            </motion.div>
          )}

          {activePanel === 'neko' && (
            <motion.div key="neko" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <NekoPanel onClose={() => setActivePanel("simulation")} />
            </motion.div>
          )}

          { activePanel === 'forge' && (
            <motion.div key="forge" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <ForgeStudioPanel onClose={() => setActivePanel("simulation")} />
            </motion.div>
          )}

          { activePanel === 'spectra' && (
            <motion.div key="spectra" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <SpectraYieldPanel spectra={state.spectra!} onClose={() => setActivePanel("simulation")} />
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Floating Side Panels & Overlays */}
      <AnimatePresence>
        {showTzinor && (
          <motion.aside
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed right-0 top-16 bottom-0 w-80 bg-[#0a0a0c] border-l border-arkhe-border/50 z-30 shadow-[-10px_0_30px_rgba(0,0,0,0.5)]"
          >
            <div className="h-full flex flex-col p-4">
               <div className="flex items-center justify-between mb-6 border-b border-arkhe-border/30 pb-4">
                 <h2 className="font-mono text-sm uppercase tracking-widest text-arkhe-orange flex items-center gap-2">
                   <Smartphone className="w-4 h-4" />
                   Tzinor Interface
                 </h2>
                 <button onClick={() => setShowTzinor(false)} className="text-arkhe-muted hover:text-white">
                   [HIDE]
                 </button>
               </div>

               <div className="flex-1 space-y-6 overflow-y-auto custom-scrollbar pr-2">
                  <ArkheCliPanel onClose={() => setShowTzinor(false)} />
                  <ResearchAgentsPanel />
                  <ZkERCSimulator onClose={() => setActivePanel("simulation")} />
                  <PolyglotCompilerPanel onClose={() => setActivePanel("simulation")} />
               </div>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showTelevision && <ArkheTVPanel onClose={() => setShowTelevision(false)} />}
      </AnimatePresence>

      <AnimatePresence>
        {showVideoGen && <VideoGenerationPanel onClose={() => setShowVideoGen(false)} />}
      </AnimatePresence>

      <AnimatePresence>
        {showTemporalStream && <TemporalStreamViewer onClose={() => setShowTemporalStream(false)} />}
      </AnimatePresence>

      <AnimatePresence>
        {showArkheOntologyVision && <ArkheOntologyVision onClose={() => setShowArkheOntologyVision(false)} />}
      </AnimatePresence>

      <AnimatePresence>
        {showChipFabricationVision && <ChipFabricationVision onClose={() => setShowChipFabricationVision(false)} />}
      </AnimatePresence>

      {/* Global Modals */}
      {state.ramsey.pendingAction && (
        <RamseyConfirmationModal
          pendingAction={state.ramsey.pendingAction}
          onClose={() => {}}
        />
      )}
    </div>
  );
}
