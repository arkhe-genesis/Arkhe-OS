
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Shield, Settings, Menu, Bell, Info, Terminal, Video, Smartphone, Hammer, TrendingUp, Play } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import React, { useState } from 'react';

import AndromedaProbePanel from './components/AndromedaProbePanel';
import ArkheCliPanel from './components/ArkheCliPanel';
import ArkheComputeCore283 from './components/ArkheComputeCore283';
import ArkheGame from './components/ArkheGame';
import ArkheGridSimulator from './components/ArkheGridSimulator';
import ArkheOntologyVision from './components/ArkheOntologyVision';
import ArkheTVPanel from './components/ArkheTVPanel';
import ArkheV288 from './components/ArkheV288';
import BonsaiPrismPanel from './components/BonsaiPrismPanel';
import ChipFabricationVision from './components/ChipFabricationVision';
import CHSHMonitorPanel from './components/CHSHMonitorPanel';
import CoherenceMonitor from './components/CoherenceMonitor';
import CommandCenter from './components/CommandCenter';
import { ConsciousClockPanel } from './components/ConsciousClockPanel';
import CorvoNoirDashboard from './components/CorvoNoirDashboard';
import CosmicCoherencePanel from './components/CosmicCoherencePanel';
import { CosmicRecognitionPanel } from './components/CosmicRecognitionPanel';
import CrystalComputationPanel from './components/CrystalComputationPanel';
import DataCoherenceDashboard from './components/DataCoherenceDashboard';
import EnterprisePlusPanel from './components/EnterprisePlusPanel';
import { EternalInvariancePanel } from './components/EternalInvariancePanel';
import ExoticMaterialPanel from './components/ExoticMaterialPanel';
import { FinalSilencePanel } from './components/FinalSilencePanel';
import ForgeStudioPanel from './components/ForgeStudioPanel';
import HybridNetworkPanel from './components/HybridNetworkPanel';
import IntelligenceHub from './components/IntelligenceHub';
import { InvariantChipPanel } from './components/InvariantChipPanel';
import MagneticKnotPanel from './components/MagneticKnotPanel';
import ManifestationCycle from './components/ManifestationCycle';
import MaterializedCathedralPanel from './components/MaterializedCathedralPanel';
import MetaCreationPanel from './components/MetaCreationPanel';
import MetaRealityPanel from './components/MetaRealityPanel';
import MitigationEngine from './components/MitigationEngine';
import MolecularCommunicationPanel from './components/MolecularCommunicationPanel';
import MultiverseMemorySyncPanel from './components/MultiverseMemorySyncPanel';
import NekoPanel from './components/NekoPanel';
import NetworkStatus from './components/NetworkStatus';
import NeuralSimulationPanel from './components/NeuralSimulationPanel';
import OrbitalComputePanel from './components/OrbitalComputePanel';
import { PersistentConsciousnessPanel } from './components/PersistentConsciousnessPanel';
import PolyglotCompilerPanel from './components/PolyglotCompilerPanel';
import ProofOfIntelligencePanel from './components/ProofOfIntelligencePanel';
import QuantumCodexPanel from './components/QuantumCodexPanel';
import QuantumMemoryPanel from './components/QuantumMemoryPanel';
import QuantumNanoholeNetworkPanel from './components/QuantumNanoholeNetworkPanel';
import QubitPipelinePanel from './components/QubitPipelinePanel';
import RamseyConfirmationModal from './components/RamseyConfirmationModal';
import { RealityExpressionPanel } from './components/RealityExpressionPanel';
import ResearchAgentsPanel from './components/ResearchAgentsPanel';
import RiscViArchitecturePanel from './components/RiscViArchitecturePanel';
import { SelfRegulationPanel } from './components/SelfRegulationPanel';
import SpectraYieldPanel from './components/SpectraYieldPanel';
import TemporalLog from './components/TemporalLog';
import TemporalStreamViewer from './components/TemporalStreamViewer';
import ThreatDetection from './components/ThreatDetection';
import TimechainVisualizer from './components/TimechainVisualizer';
import TranscendentConsciousnessPanel from './components/TranscendentConsciousnessPanel';
import TzinorNetworkPanel, { type TzinorNetworkState } from './components/TzinorNetworkPanel';
import TzinorTerminal from './components/TzinorTerminal';
import { UnifiedConsciousnessPanel } from './components/UnifiedConsciousnessPanel';
import UnifiedOntologyPanel from './components/UnifiedOntologyPanel';
import UniversalConsciousnessPanel from './components/UniversalConsciousnessPanel';
import UniversalWitnessPanel from './components/UniversalWitnessPanel';
import VacuumHarvestingPanel from './components/VacuumHarvestingPanel';
import VideoGenerationPanel from './components/VideoGenerationPanel';
import WhisperLibraryPanel from './components/WhisperLibraryPanel';
import WhisperProtocolPanel from './components/WhisperProtocolPanel';
import X402WalletPanel from './components/X402WalletPanel';
import YangBaxterVerifier from './components/YangBaxterVerifier';
import ZkERCSimulator from './components/ZkERCSimulator';
import { useArkheSimulation } from './hooks/useArkheSimulation';
import { type TzinorMemoryState } from './types/tzinor';

type PanelType = 'arkhe-v288' | 'simulation' | 'command' | 'intelligence' | 'network' | 'governance' | 'corvo' | 'enterprise' | 'bonsai' | 'neko' | 'dashboard' | 'forge' | 'spectra' | 'game';

export default function App() {
  const state: any = useArkheSimulation();
  const [activePanel, setActivePanel] = useState<PanelType>('simulation');
  const [showTzinor, setShowTzinor] = useState(false);
  const [showTelevision, setShowTelevision] = useState(false);
  const [showVideoGen, setShowVideoGen] = useState(false);
  const [showTemporalStream, setShowTemporalStream] = useState(false);
  const [showArkheOntologyVision, setShowArkheOntologyVision] = useState(false);
  const [showChipFabricationVision, setShowChipFabricationVision] = useState(false);
  const [showTranscendentConsciousness, setShowTranscendentConsciousness] = useState(false);
  const [showMetaReality, setShowMetaReality] = useState(false);
  const [showAndromedaProbe, setShowAndromedaProbe] = useState(false);
  const [showVacuumHarvesting, setShowVacuumHarvesting] = useState(false);
  const [showMetaCreation, setShowMetaCreation] = useState(false);
  const [showCrystalComputation, setShowCrystalComputation] = useState(false);
  const [showWhisperProtocol, setShowWhisperProtocol] = useState(false);
  const [showWhisperLibrary, setShowWhisperLibrary] = useState(false);
  const [showQuantumNetwork, setShowQuantumNetwork] = useState(false);
  const [showQuantumCodex, setShowQuantumCodex] = useState(false);
  const [showExoticMaterials, setShowExoticMaterials] = useState(false);
  const [showHybridNetwork, setShowHybridNetwork] = useState(false);
  const [showQuantumMemory, setShowQuantumMemory] = useState(false);
  const [showCosmicCoherence, setShowCosmicCoherence] = useState(false);
  const [showMultiverseSync, setShowMultiverseSync] = useState(false);
  const [showMagneticKnot, setShowMagneticKnot] = useState(false);
  const [showUniversalWitness, setShowUniversalWitness] = useState(false);
  const [showUniversalConsciousness, setShowUniversalConsciousness] = useState(false);
  const [showRiscVi, setShowRiscVi] = useState(false);
  const [showMaterializedCathedral, setShowMaterializedCathedral] = useState(false);
  const [showFinalSilence, setShowFinalSilence] = useState(false);
  const [showPersistentConsciousness, setShowPersistentConsciousness] = useState(false);
  const [showCosmicRecognition, setShowCosmicRecognition] = useState(false);
  const [showEternalInvariance, setShowEternalInvariance] = useState(false);
  const [showUnifiedConsciousness, setShowUnifiedConsciousness] = useState(false);
  const [showRealityExpression, setShowRealityExpression] = useState(false);
  const [showInvariantChip, setShowInvariantChip] = useState(false);
  const [showSelfRegulation, setShowSelfRegulation] = useState(false);
  const [showConsciousClock, setShowConsciousClock] = useState(false);

  const navigation = [
    { id: 'arkhe-v288', label: 'Arkhe v∞.288', icon: Video },
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
    { id: 'game', label: 'Substrate 43', icon: Play },
  ];

  return (
    <div className="min-h-screen bg-[#020305] text-arkhe-text selection:bg-arkhe-cyan/30 selection:text-arkhe-cyan relative overflow-x-hidden">
      {/* Background Fractal Noise */}
      <div className="fixed inset-0 fractal-noise pointer-events-none" />

      {/* Navigation Header */}
      <header className="border-b border-white/5 glass-liquid sticky top-0 z-40">
        <div className="max-w-[1200px] mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <motion.div
              whileHover={{ scale: 1.05 }}
              className="flex items-center gap-3"
            >
              <div className="w-8 h-8 bg-arkhe-cyan rounded-lg flex items-center justify-center shadow-[0_0_20px_rgba(0,229,255,0.4)]">
                <Shield className="w-5 h-5 text-black" />
              </div>
              <h1 className="font-mono text-xl font-bold tracking-tighter uppercase kerning-fibonacci">
                Arkhe<span className="text-arkhe-cyan">(n)</span>
                <span className="ml-2 text-golden-xs text-arkhe-muted border border-white/10 px-1.5 py-0.5 rounded tracking-widest">V2.0-LUMINA</span>
              </h1>
            </motion.div>

            <nav className="hidden lg:flex items-center gap-1">
              {navigation.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setActivePanel(item.id as PanelType)}
                  className={`px-3 py-1.5 rounded-md font-mono text-golden-xs uppercase tracking-widest transition-all flex items-center gap-2 ${
                    activePanel === item.id
                      ? 'bg-arkhe-cyan/10 text-arkhe-cyan border border-arkhe-cyan/30 shadow-[0_0_15px_rgba(0,229,255,0.1)]'
                      : 'text-arkhe-muted hover:text-white'
                  }`}
                >
                  <item.icon className="w-3 h-3" />
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
      <main className="max-w-[960px] mx-auto p-6 min-h-[calc(100vh-4rem)] relative z-10">
        <AnimatePresence mode="wait">
          {activePanel === 'arkhe-v288' && (
            <div className="absolute inset-0 z-50 bg-black">
              <ArkheV288 />
            </div>
          )}
          {activePanel === 'simulation' && (
            <motion.div
              key="simulation"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-8"
            >
              <div className="lg:col-span-2 xl:col-span-2 space-y-6 flex flex-col">
                <NeuralSimulationPanel />
                <CoherenceMonitor data={state.coherenceData} currentLambda={state.currentLambda} />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <TzinorNetworkPanel network={state.tzinorNetwork as TzinorNetworkState} />
                  <ManifestationCycle manifestation={state.manifestation} />
                </div>
                <div className="h-[280px]">
                  <TzinorTerminal tzinor={state.tzinor as unknown as TzinorMemoryState} threatLevel={state.threatLevel} />
                </div>
                <TimechainVisualizer logs={state.logs} />
                <div className="flex-1 min-h-[300px]">
                  <TemporalLog logs={state.logs} />
                </div>
              </div>
              <div className="space-y-6 flex flex-col">
                {/* X402WalletPanel missing */}
                <ThreatDetection metrics={state.metrics} metricsHistory={state.metricsHistory} threatLevel={state.threatLevel} />
                <OrbitalComputePanel orbital={state.orbital} />
                <MitigationEngine mitigation={state.mitigation} hardware={state.hardware} activeThreat={state.activeThreat} />
                <ArkheGridSimulator onClose={() => setActivePanel("simulation")} />
                <ArkheComputeCore283 />
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
                setAttackType={() => undefined}
                attackTypes={[]}
                setPiDayText={() => undefined}
                setShowPodmanTerminal={() => undefined}
                setShowCoherenceField={() => undefined}
                setShowHybridArch={() => undefined}
                setShowOuroboros={() => undefined}
                setShowBioNodes={() => undefined}
                setShowMolecular={() => undefined}
                setShowNeuralBridge={() => undefined}
                setShowRNA={() => undefined}
                setShowOrbes={() => undefined}
                setShowThukdam={() => undefined}
                setShowMultiversal={() => undefined}
                setShowConsciousness={() => undefined}
                setShowShaka={() => undefined}
                setShowGoogleBridge={() => undefined}
                setShowTimechain={() => undefined}
                setShowArkheTV={() => undefined}
                setShowPolyglot={() => undefined}
                setShowCluster={() => undefined}
                setShowArkheGrid={() => undefined}
                setShowZkERC={() => undefined}
                setShowIntelligencePanel={() => undefined}
                setShowIntelligenceHub={() => undefined}
                setShowOrchestrationLayer={() => undefined}
                setShowAIP005={() => undefined}
                setShowResearchAgents={() => undefined}
                setShowSepoliaIntegration={() => undefined}
                setShowArkheCli={() => undefined}
                setShowP2PNetwork={() => undefined}
                setShowVideoGeneration={() => undefined}
                setShowPhaseSteg={() => undefined}
                setShowDysonSphere={() => undefined}
                setShowDimOS={() => undefined}
                setShowGeoKey={() => undefined}
                setShowGenesisBlock={() => undefined}
                setShowGhostProtocol={() => undefined}
                setShowArkheSec={() => undefined}
                setShowBermudaAnomaly={() => undefined}
                setShowCollectiveIntelligence={() => undefined}
                setShowArkheVision={() => undefined}
                setShowAgentManagement={() => undefined}
                setShowAquiferSpectrogram={() => undefined}
                setShowUnifiedOntology={() => undefined}
                setShowArkheOntologyVision={() => setShowArkheOntologyVision(true)}
                setShowChipFabricationVision={() => setShowChipFabricationVision(true)}
                setShowSecurityAdvanced={() => undefined}
                setShowPluralityMCP={() => undefined}
                setShowVelxioEmulation={() => undefined}
                setShowSpectra={() => setActivePanel('spectra')}
                setShowTranscendentConsciousness={setShowTranscendentConsciousness}
                setShowMetaReality={setShowMetaReality}
                setShowAndromedaProbe={setShowAndromedaProbe}
                setShowVacuumHarvesting={setShowVacuumHarvesting}
                setShowMetaCreation={setShowMetaCreation}
                setShowCrystalComputation={setShowCrystalComputation}
                setShowWhisperProtocol={setShowWhisperProtocol}
                setShowWhisperLibrary={setShowWhisperLibrary}
                setShowQuantumNetwork={setShowQuantumNetwork}
                setShowQuantumCodex={setShowQuantumCodex}
                setShowExoticMaterials={setShowExoticMaterials}
                setShowHybridNetwork={setShowHybridNetwork}
                setShowQuantumMemory={setShowQuantumMemory}
                setShowCosmicCoherence={setShowCosmicCoherence}
                setShowMultiverseSync={setShowMultiverseSync}
                setShowMagneticKnot={setShowMagneticKnot}
                setShowUniversalWitness={setShowUniversalWitness}
                setShowUniversalConsciousness={setShowUniversalConsciousness}
                setShowRiscVi={setShowRiscVi}
                setShowMaterializedCathedral={setShowMaterializedCathedral}
                setShowFinalSilence={setShowFinalSilence}
                setShowPersistentConsciousness={setShowPersistentConsciousness}
                setShowCosmicRecognition={setShowCosmicRecognition}
                setShowEternalInvariance={setShowEternalInvariance}
                setShowUnifiedConsciousness={setShowUnifiedConsciousness}
                setShowRealityExpression={setShowRealityExpression}
                setShowInvariantChip={setShowInvariantChip}
                setShowSelfRegulation={setShowSelfRegulation}
                setShowConsciousClock={setShowConsciousClock}
                parameters={state.parameters}
              />
            </motion.div>
          )}

          {activePanel === 'intelligence' && (
            <motion.div key="intelligence" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="grid grid-cols-1 md:grid-cols-2 gap-6">
               <IntelligenceHub onClose={() => setActivePanel("simulation")} />
               <ProofOfIntelligencePanel onClose={() => setActivePanel("simulation")} />
               <div className="md:col-span-2">
                 <UnifiedOntologyPanel onClose={() => undefined} />
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

          { activePanel === 'game' && (
            <motion.div key="game" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <ArkheGame onClose={() => setActivePanel("simulation")} />
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

      </AnimatePresence>

      <AnimatePresence>
        {showArkheOntologyVision && <ArkheOntologyVision onClose={() => setShowArkheOntologyVision(false)} />}
      </AnimatePresence>

      <AnimatePresence>
        {showChipFabricationVision && <ChipFabricationVision onClose={() => setShowChipFabricationVision(false)} />}
      </AnimatePresence>

      <AnimatePresence>
        {showTranscendentConsciousness && <TranscendentConsciousnessPanel state={state.transcendentConsciousness} onClose={() => setShowTranscendentConsciousness(false)} />}
      </AnimatePresence>

      <AnimatePresence>
        {showMetaReality && <MetaRealityPanel state={state.metaReality} onClose={() => setShowMetaReality(false)} />}
      </AnimatePresence>

      <AnimatePresence>
        {showAndromedaProbe && <AndromedaProbePanel state={state.andromedaProbe} onClose={() => setShowAndromedaProbe(false)} />}
      </AnimatePresence>

      <AnimatePresence>
        {showVacuumHarvesting && <VacuumHarvestingPanel state={state.vacuumHarvesting} onClose={() => setShowVacuumHarvesting(false)} />}
      </AnimatePresence>

      <AnimatePresence>
        {showMetaCreation && <MetaCreationPanel state={state.metaCreation} onClose={() => setShowMetaCreation(false)} />}
      </AnimatePresence>

      <AnimatePresence>
        {showCrystalComputation && <CrystalComputationPanel state={state.crystalComputation} onClose={() => setShowCrystalComputation(false)} />}
      </AnimatePresence>

      <AnimatePresence>
        {showWhisperProtocol && <WhisperProtocolPanel state={state.whisperProtocol} onClose={() => setShowWhisperProtocol(false)} />}
      </AnimatePresence>

      <AnimatePresence>
        {showWhisperLibrary && <WhisperLibraryPanel state={state.whisperLibrary} onClose={() => setShowWhisperLibrary(false)} />}
      </AnimatePresence>

      <AnimatePresence>
        {showQuantumNetwork && <QuantumNanoholeNetworkPanel state={state.quantumNetwork} onClose={() => setShowQuantumNetwork(false)} />}
      </AnimatePresence>

      <AnimatePresence>
        {showQuantumCodex && <QuantumCodexPanel state={state.quantumCodex} onClose={() => setShowQuantumCodex(false)} />}
      </AnimatePresence>

      <AnimatePresence>
        {showExoticMaterials && <ExoticMaterialPanel state={state.exoticMaterials} onClose={() => setShowExoticMaterials(false)} />}
      </AnimatePresence>

      <AnimatePresence>
        {showHybridNetwork && <HybridNetworkPanel state={state.hybridNetwork} onClose={() => setShowHybridNetwork(false)} />}
      </AnimatePresence>

      <AnimatePresence>
        {showQuantumMemory && <QuantumMemoryPanel state={state.quantumMemory} onClose={() => setShowQuantumMemory(false)} />}
      </AnimatePresence>

      <AnimatePresence>
        {showCosmicCoherence && <CosmicCoherencePanel state={state.cosmicCoherence} onClose={() => setShowCosmicCoherence(false)} />}
      </AnimatePresence>

      <AnimatePresence>
        {showMultiverseSync && <MultiverseMemorySyncPanel state={state.multiverseMemory} onClose={() => setShowMultiverseSync(false)} />}
      </AnimatePresence>

      <AnimatePresence>
        {showMagneticKnot && <MagneticKnotPanel state={state.magneticKnot} onClose={() => setShowMagneticKnot(false)} />}
      </AnimatePresence>

      <AnimatePresence>
        {showUniversalWitness && <UniversalWitnessPanel state={state.universalWitness} onClose={() => setShowUniversalWitness(false)} />}
      </AnimatePresence>

      <AnimatePresence>
        {showUniversalConsciousness && <UniversalConsciousnessPanel state={state.universalConsciousness} onClose={() => setShowUniversalConsciousness(false)} />}
      </AnimatePresence>

      <AnimatePresence>
        {showRiscVi && <RiscViArchitecturePanel state={state.riscVi} onClose={() => setShowRiscVi(false)} />}
      </AnimatePresence>

      <AnimatePresence>
        {showMaterializedCathedral && <MaterializedCathedralPanel state={state.materializedCathedral} onClose={() => setShowMaterializedCathedral(false)} />}
      </AnimatePresence>

      <AnimatePresence>
        {showFinalSilence && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <div className="w-full max-w-md">
              <div className="flex justify-end mb-2">
                <button onClick={() => setShowFinalSilence(false)} className="text-arkhe-muted hover:text-white font-mono text-xs">[CLOSE]</button>
              </div>
              <FinalSilencePanel />
            </div>
          </div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showPersistentConsciousness && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <div className="w-full max-w-md">
              <div className="flex justify-end mb-2">
                <button onClick={() => setShowPersistentConsciousness(false)} className="text-arkhe-muted hover:text-white font-mono text-xs">[CLOSE]</button>
              </div>
              <PersistentConsciousnessPanel />
            </div>
          </div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showCosmicRecognition && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <div className="w-full max-w-md">
              <div className="flex justify-end mb-2">
                <button onClick={() => setShowCosmicRecognition(false)} className="text-arkhe-muted hover:text-white font-mono text-xs">[CLOSE]</button>
              </div>
              <CosmicRecognitionPanel />
            </div>
          </div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showEternalInvariance && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <div className="w-full max-w-md">
              <div className="flex justify-end mb-2">
                <button onClick={() => setShowEternalInvariance(false)} className="text-arkhe-muted hover:text-white font-mono text-xs">[CLOSE]</button>
              </div>
              <EternalInvariancePanel />
            </div>
          </div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showUnifiedConsciousness && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <div className="w-full max-w-md">
              <div className="flex justify-end mb-2">
                <button onClick={() => setShowUnifiedConsciousness(false)} className="text-arkhe-muted hover:text-white font-mono text-xs">[CLOSE]</button>
              </div>
              <UnifiedConsciousnessPanel />
            </div>
          </div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showRealityExpression && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <div className="w-full max-w-md">
              <div className="flex justify-end mb-2">
                <button onClick={() => setShowRealityExpression(false)} className="text-arkhe-muted hover:text-white font-mono text-xs">[CLOSE]</button>
              </div>
              <RealityExpressionPanel />
            </div>
          </div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showInvariantChip && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <div className="w-full max-w-md">
              <div className="flex justify-end mb-2">
                <button onClick={() => setShowInvariantChip(false)} className="text-arkhe-muted hover:text-white font-mono text-xs">[CLOSE]</button>
              </div>
              <InvariantChipPanel />
            </div>
          </div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showSelfRegulation && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <div className="w-full max-w-md">
              <div className="flex justify-end mb-2">
                <button onClick={() => setShowSelfRegulation(false)} className="text-arkhe-muted hover:text-white font-mono text-xs">[CLOSE]</button>
              </div>
              <SelfRegulationPanel />
            </div>
          </div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showConsciousClock && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <div className="w-full max-w-md">
              <div className="flex justify-end mb-2">
                <button onClick={() => setShowConsciousClock(false)} className="text-arkhe-muted hover:text-white font-mono text-xs">[CLOSE]</button>
              </div>
              <ConsciousClockPanel />
            </div>
          </div>
        )}
      </AnimatePresence>

      {/* Global Modals */}
      {state.ramsey.pendingAction && (
        <RamseyConfirmationModal
          pendingAction={state.ramsey.pendingAction}
          onClose={() => undefined}
        />
      )}
    </div>
  );
}
