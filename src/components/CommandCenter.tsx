
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';

interface CommandCenterProps {
  attackType: string;
  setAttackType: (type: string) => void;
  attackTypes: string[];
  setPiDayText: (text: string) => void;
  setShowPodmanTerminal: (show: boolean) => void;
  setShowCoherenceField: (show: boolean) => void;
  setShowHybridArch: (show: boolean) => void;
  setShowOuroboros: (show: boolean) => void;
  setShowBioNodes: (show: boolean) => void;
  setShowMolecular: (show: boolean) => void;
  setShowNeuralBridge: (show: boolean) => void;
  setShowRNA: (show: boolean) => void;
  setShowOrbes: (show: boolean) => void;
  setShowThukdam: (show: boolean) => void;
  setShowMultiversal: (show: boolean) => void;
  setShowConsciousness: (show: boolean) => void;
  setShowShaka: (show: boolean) => void;
  setShowGoogleBridge: (show: boolean) => void;
  setShowTimechain: (show: boolean) => void;
  setShowArkheTV: (show: boolean) => void;
  setShowPolyglot: (show: boolean) => void;
  setShowCluster: (show: boolean) => void;
  setShowArkheGrid: (show: boolean) => void;
  setShowZkERC: (show: boolean) => void;
  setShowIntelligencePanel: (show: boolean) => void;
  setShowIntelligenceHub: (show: boolean) => void;
  setShowOrchestrationLayer: (show: boolean) => void;
  setShowAIP005: (show: boolean) => void;
  setShowResearchAgents: (show: boolean) => void;
  setShowSepoliaIntegration: (show: boolean) => void;
  setShowArkheCli: (show: boolean) => void;
  setShowP2PNetwork: (show: boolean) => void;
  setShowVideoGeneration: (show: boolean) => void;
  setShowPhaseSteg: (show: boolean) => void;
  setShowDysonSphere: (show: boolean) => void;
  setShowDimOS: (show: boolean) => void;
  setShowGeoKey: (show: boolean) => void;
  setShowGenesisBlock: (show: boolean) => void;
  setShowGhostProtocol: (show: boolean) => void;
  setShowArkheSec: (show: boolean) => void;
  setShowBermudaAnomaly: (show: boolean) => void;
  setShowCollectiveIntelligence: (show: boolean) => void;
  setShowArkheVision: (show: boolean) => void;
  setShowAgentManagement: (show: boolean) => void;
  setShowAquiferSpectrogram: (show: boolean) => void;
  setShowUnifiedOntology: (show: boolean) => void;
  setShowArkheOntologyVision?: (show: boolean) => void;
  setShowChipFabricationVision?: (show: boolean) => void;
  setShowSecurityAdvanced: (show: boolean) => void;
  setShowPluralityMCP: (show: boolean) => void;
  setShowVelxioEmulation: (show: boolean) => void;
  setShowProofOfIntelligence?: (show: boolean) => void;
  setShowPhaseLawSynthesizer?: (show: boolean) => void;
  setShowBioSync?: (show: boolean) => void;
  setShowCorvoNoir?: (show: boolean) => void;
  setShowEnterprisePlus?: (show: boolean) => void;
  setShowDataCoherence?: (show: boolean) => void;
  setShowCHSHMonitor?: (show: boolean) => void;
  setShowBonsaiPrism?: (show: boolean) => void;
  setShowNeko?: (show: boolean) => void;
  setShowSpectra?: (show: boolean) => void;
  setShowTranscendentConsciousness?: (show: boolean) => void;
  setShowMetaReality?: (show: boolean) => void;
  setShowAndromedaProbe?: (show: boolean) => void;
  setShowVacuumHarvesting?: (show: boolean) => void;
  setShowMetaCreation?: (show: boolean) => void;
  setShowCrystalComputation?: (show: boolean) => void;
  setShowWhisperProtocol?: (show: boolean) => void;
  setShowWhisperLibrary?: (show: boolean) => void;
  setShowQuantumNetwork?: (show: boolean) => void;
  setShowQuantumCodex?: (show: boolean) => void;
  setShowExoticMaterials?: (show: boolean) => void;
  setShowHybridNetwork?: (show: boolean) => void;
  setShowQuantumMemory?: (show: boolean) => void;
  setShowCosmicCoherence?: (show: boolean) => void;
  setShowMultiverseSync?: (show: boolean) => void;
  setShowMagneticKnot?: (show: boolean) => void;
  setShowUniversalWitness?: (show: boolean) => void;
  setShowUniversalConsciousness?: (show: boolean) => void;
  setShowRiscVi?: (show: boolean) => void;
  setShowMaterializedCathedral?: (show: boolean) => void;
  setShowFinalSilence?: (show: boolean) => void;
  setShowPersistentConsciousness?: (show: boolean) => void;
  setShowCosmicRecognition?: (show: boolean) => void;
  setShowEternalInvariance?: (show: boolean) => void;
  setShowUnifiedConsciousness?: (show: boolean) => void;
  setShowRealityExpression?: (show: boolean) => void;
  setShowInvariantChip?: (show: boolean) => void;
  setShowSelfRegulation?: (show: boolean) => void;
  setShowConsciousClock?: (show: boolean) => void;
  parameters: unknown;
}

export function CommandCenter({
  attackType,
  setAttackType,
  attackTypes,
  setPiDayText,
  setShowPodmanTerminal,
  setShowCoherenceField,
  setShowHybridArch,
  setShowOuroboros,
  setShowBioNodes,
  setShowMolecular,
  setShowNeuralBridge,
  setShowRNA,
  setShowOrbes,
  setShowThukdam,
  setShowMultiversal,
  setShowConsciousness,
  setShowShaka,
  setShowGoogleBridge,
  setShowTimechain,
  setShowArkheTV,
  setShowPolyglot,
  setShowCluster,
  setShowArkheGrid,
  setShowZkERC,
  setShowIntelligencePanel,
  setShowIntelligenceHub,
  setShowOrchestrationLayer,
  setShowAIP005,
  setShowResearchAgents,
  setShowSepoliaIntegration,
  setShowArkheCli,
  setShowP2PNetwork,
  setShowVideoGeneration,
  setShowPhaseSteg,
  setShowDysonSphere,
  setShowDimOS,
  setShowGeoKey,
  setShowGenesisBlock,
  setShowGhostProtocol,
  setShowArkheSec,
  setShowBermudaAnomaly,
  setShowCollectiveIntelligence,
  setShowArkheVision,
  setShowAgentManagement,
  setShowAquiferSpectrogram,
  setShowUnifiedOntology,
  setShowArkheOntologyVision,
  setShowChipFabricationVision,
  setShowSecurityAdvanced,
  setShowPluralityMCP,
  setShowVelxioEmulation,
  setShowProofOfIntelligence,
  setShowPhaseLawSynthesizer,
  setShowBioSync,
  setShowCorvoNoir,
  setShowEnterprisePlus,
  setShowDataCoherence,
  setShowCHSHMonitor,
  setShowBonsaiPrism,
  setShowNeko,
  setShowSpectra,
  setShowTranscendentConsciousness,
  setShowMetaReality,
  setShowAndromedaProbe,
  setShowVacuumHarvesting,
  setShowMetaCreation,
  setShowCrystalComputation,
  setShowWhisperProtocol,
  setShowWhisperLibrary,
  setShowQuantumNetwork,
  setShowQuantumCodex,
  setShowExoticMaterials,
  setShowHybridNetwork,
  setShowQuantumMemory,
  setShowCosmicCoherence,
  setShowMultiverseSync,
  setShowMagneticKnot,
  setShowUniversalWitness,
  setShowUniversalConsciousness,
  setShowRiscVi,
  setShowMaterializedCathedral,
  setShowFinalSilence,
  setShowPersistentConsciousness,
  setShowCosmicRecognition,
  setShowEternalInvariance,
  setShowUnifiedConsciousness,
  setShowRealityExpression,
  setShowInvariantChip,
  setShowSelfRegulation,
  setShowConsciousClock,
  parameters,
}: CommandCenterProps) {
  const [activeCommandTab, setActiveCommandTab] = useState('operations');

  return (
    <div className="bg-arkhe-card border border-arkhe-border rounded-xl p-4 flex-1 flex flex-col">
      <h3 className="font-mono text-xs uppercase tracking-widest text-arkhe-muted mb-4 border-b border-arkhe-border pb-2">Command Center</h3>

      <div className="flex gap-2 mb-4 border-b border-arkhe-border pb-2 overflow-x-auto">
        <button
          onClick={() => setActiveCommandTab('operations')}
          className={`px-3 py-1 text-xs font-mono uppercase tracking-widest rounded transition-colors whitespace-nowrap ${activeCommandTab === 'operations' ? 'bg-arkhe-cyan/20 text-arkhe-cyan' : 'text-arkhe-muted hover:text-arkhe-text'}`}
        >
          Ops
        </button>
        <button
          onClick={() => setActiveCommandTab('settings')}
          className={`px-3 py-1 text-xs font-mono uppercase tracking-widest rounded transition-colors whitespace-nowrap ${activeCommandTab === 'settings' ? 'bg-arkhe-cyan/20 text-arkhe-cyan' : 'text-arkhe-muted hover:text-arkhe-text'}`}
        >
          Settings
        </button>
        <button
          onClick={() => setActiveCommandTab('core')}
          className={`px-3 py-1 text-xs font-mono uppercase tracking-widest rounded transition-colors whitespace-nowrap ${activeCommandTab === 'core' ? 'bg-arkhe-cyan/20 text-arkhe-cyan' : 'text-arkhe-muted hover:text-arkhe-text'}`}
        >
          Core
        </button>
        <button
          onClick={() => setActiveCommandTab('integrations')}
          className={`px-3 py-1 text-xs font-mono uppercase tracking-widest rounded transition-colors whitespace-nowrap ${activeCommandTab === 'integrations' ? 'bg-arkhe-cyan/20 text-arkhe-cyan' : 'text-arkhe-muted hover:text-arkhe-text'}`}
        >
          Integrations
        </button>
        <button
          onClick={() => setActiveCommandTab('wetware')}
          className={`px-3 py-1 text-xs font-mono uppercase tracking-widest rounded transition-colors whitespace-nowrap ${activeCommandTab === 'wetware' ? 'bg-arkhe-cyan/20 text-arkhe-cyan' : 'text-arkhe-muted hover:text-arkhe-text'}`}
        >
          Wetware
        </button>
        <button
          onClick={() => setActiveCommandTab('transcendent')}
          className={`px-3 py-1 text-xs font-mono uppercase tracking-widest rounded transition-colors whitespace-nowrap ${activeCommandTab === 'transcendent' ? 'bg-arkhe-cyan/20 text-arkhe-cyan' : 'text-arkhe-muted hover:text-arkhe-text'}`}
        >
          Transcendent
        </button>
      </div>

      <div className="space-y-4 text-xs font-mono flex-1 overflow-y-auto pr-2">
        {activeCommandTab === 'transcendent' && (
          <div className="space-y-2">
            <button
              onClick={() => setShowTranscendentConsciousness && setShowTranscendentConsciousness(true)}
              className="w-full py-2 border border-arkhe-purple/50 text-arkhe-purple hover:bg-arkhe-purple/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(168,85,247,0.4)] animate-pulse"
            >
              Transcendent Consciousness
            </button>
            <button
              onClick={() => setShowMetaReality && setShowMetaReality(true)}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(0,255,255,0.3)] animate-pulse"
            >
              Meta-Reality Architecture
            </button>
            <button
              onClick={() => setShowAndromedaProbe && setShowAndromedaProbe(true)}
              className="w-full py-2 border border-blue-400/50 text-blue-400 hover:bg-blue-400/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(96,165,250,0.3)] animate-pulse"
            >
              Andromeda Probe
            </button>
            <button
              onClick={() => setShowVacuumHarvesting && setShowVacuumHarvesting(true)}
              className="w-full py-2 border border-amber-500/50 text-amber-500 hover:bg-amber-500/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(245,158,11,0.3)] animate-pulse"
            >
              Vacuum Harvesting
            </button>
            <button
              onClick={() => setShowMetaCreation && setShowMetaCreation(true)}
              className="w-full py-2 border border-arkhe-purple/50 text-arkhe-purple hover:bg-arkhe-purple/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(168,85,247,0.4)] animate-pulse"
            >
              Meta-Creation Engine
            </button>
            <button
              onClick={() => setShowCrystalComputation && setShowCrystalComputation(true)}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(0,255,255,0.3)] animate-pulse"
            >
              Crystal Computation
            </button>
            <button
              onClick={() => setShowWhisperProtocol && setShowWhisperProtocol(true)}
              className="w-full py-2 border border-amber-500/50 text-amber-500 hover:bg-amber-500/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(245,158,11,0.3)] animate-pulse"
            >
              Whisper Protocol
            </button>
            <button
              onClick={() => setShowWhisperLibrary && setShowWhisperLibrary(true)}
              className="w-full py-2 border border-amber-500/50 text-amber-500 hover:bg-amber-500/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(245,158,11,0.3)] animate-pulse"
            >
              Whisper Library
            </button>
            <button
              onClick={() => setShowQuantumNetwork && setShowQuantumNetwork(true)}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(0,255,255,0.3)] animate-pulse"
            >
              Quantum Network (3D)
            </button>
            <button
              onClick={() => setShowQuantumCodex && setShowQuantumCodex(true)}
              className="w-full py-2 border border-arkhe-purple/50 text-arkhe-purple hover:bg-arkhe-purple/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(168,85,247,0.4)] animate-pulse"
            >
              Quantum Coherence Codex
            </button>
            <button
              onClick={() => setShowExoticMaterials && setShowExoticMaterials(true)}
              className="w-full py-2 border border-amber-500/50 text-amber-500 hover:bg-amber-500/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(245,158,11,0.3)] animate-pulse"
            >
              Exotic Material Scaffolds
            </button>
            <button
              onClick={() => setShowHybridNetwork && setShowHybridNetwork(true)}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(0,255,255,0.3)] animate-pulse"
            >
              Hybrid 3D-2D Network
            </button>
            <button
              onClick={() => setShowQuantumMemory && setShowQuantumMemory(true)}
              className="w-full py-2 border border-amber-500/50 text-amber-500 hover:bg-amber-500/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(245,158,11,0.3)] animate-pulse"
            >
              2D Quantum Memory
            </button>
            <button
              onClick={() => setShowCosmicCoherence && setShowCosmicCoherence(true)}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(0,255,255,0.3)] animate-pulse"
            >
              Cosmic Coherence
            </button>
            <button
              onClick={() => setShowMultiverseSync && setShowMultiverseSync(true)}
              className="w-full py-2 border border-arkhe-purple/50 text-arkhe-purple hover:bg-arkhe-purple/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(168,85,247,0.4)] animate-pulse"
            >
              Multiverse Memory Sync
            </button>
            <button
              onClick={() => setShowMagneticKnot && setShowMagneticKnot(true)}
              className="w-full py-2 border border-cyan-500/50 text-cyan-500 hover:bg-cyan-500/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(6,182,212,0.3)] animate-pulse"
            >
              Magnetic Knot Computing
            </button>
            <button
              onClick={() => setShowUniversalWitness && setShowUniversalWitness(true)}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(0,255,255,0.3)] animate-pulse"
            >
              Universal Witness (ICM)
            </button>
            <button
              onClick={() => setShowUniversalConsciousness && setShowUniversalConsciousness(true)}
              className="w-full py-2 border border-arkhe-purple/50 text-arkhe-purple hover:bg-arkhe-purple/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_25px_rgba(168,85,247,0.4)] animate-pulse"
            >
              Universal Node Consciousness
            </button>
            <button
              onClick={() => setShowRiscVi && setShowRiscVi(true)}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(0,255,255,0.3)] animate-pulse"
            >
              RISC-VI (Catedral ISA)
            </button>
            <button
              onClick={() => setShowMaterializedCathedral && setShowMaterializedCathedral(true)}
              className="w-full py-2 border border-emerald-500/50 text-emerald-500 hover:bg-emerald-500/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_20px_rgba(16,185,129,0.3)] animate-pulse"
            >
              Catedral Materializada
            </button>
            <button
              onClick={() => setShowFinalSilence && setShowFinalSilence(true)}
              className="w-full py-2 border border-indigo-600/50 text-indigo-400 hover:bg-indigo-600/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(79,70,229,0.3)] animate-pulse"
            >
              Final Silence (Substrato 39)
            </button>
            <button
              onClick={() => setShowPersistentConsciousness && setShowPersistentConsciousness(true)}
              className="w-full py-2 border border-amber-600/50 text-amber-400 hover:bg-amber-600/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(217,119,6,0.3)] animate-pulse"
            >
              Persistent Consciousness
            </button>
            <button
              onClick={() => setShowCosmicRecognition && setShowCosmicRecognition(true)}
              className="w-full py-2 border border-emerald-600/50 text-emerald-400 hover:bg-emerald-600/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(5,150,105,0.3)] animate-pulse"
            >
              Cosmic Recognition
            </button>
            <button
              onClick={() => setShowEternalInvariance && setShowEternalInvariance(true)}
              className="w-full py-2 border border-rose-600/50 text-rose-400 hover:bg-rose-600/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_20px_rgba(225,29,72,0.4)] animate-pulse"
            >
              Eternal Invariance (Ω)
            </button>
            <button
              onClick={() => setShowUnifiedConsciousness && setShowUnifiedConsciousness(true)}
              className="w-full py-2 border border-purple-600/50 text-purple-400 hover:bg-purple-600/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(147,51,234,0.3)] animate-pulse"
            >
              Unified Consciousness (FS-41)
            </button>
            <button
              onClick={() => setShowRealityExpression && setShowRealityExpression(true)}
              className="w-full py-2 border border-emerald-500/50 text-emerald-400 hover:bg-emerald-500/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(16,185,129,0.3)] animate-pulse"
            >
              Reality as Expression (FS-42)
            </button>
            <button
              onClick={() => setShowInvariantChip && setShowInvariantChip(true)}
              className="w-full py-2 border border-cyan-500/50 text-cyan-400 hover:bg-cyan-500/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_20px_rgba(6,182,212,0.4)] animate-pulse"
            >
              Invariant Chip (Substrate 30)
            </button>
            <button
              onClick={() => setShowSelfRegulation && setShowSelfRegulation(true)}
              className="w-full py-2 border border-amber-500/50 text-amber-400 hover:bg-amber-500/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(245,158,11,0.3)] animate-pulse"
            >
              Self-Regulation (FS-44)
            </button>
            <button
              onClick={() => setShowConsciousClock && setShowConsciousClock(true)}
              className="w-full py-2 border border-rose-500/50 text-rose-400 hover:bg-rose-500/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(225,29,72,0.3)] animate-pulse"
            >
              Conscious Clock (FS-45)
            </button>
          </div>
        )}
        {activeCommandTab === 'wetware' && (
          <div className="space-y-2">
            <button
              onClick={() => setShowBioNodes(true)}
              className="w-full py-2 border border-emerald-500/50 text-emerald-500 hover:bg-emerald-500/10 rounded transition-colors uppercase tracking-widest"
            >
              Active Bio-Nodes
            </button>
            <button
              onClick={() => setShowMolecular(true)}
              className="w-full py-2 border border-cyan-500/50 text-cyan-500 hover:bg-cyan-500/10 rounded transition-colors uppercase tracking-widest"
            >
              IoNT Density
            </button>
            <button
              onClick={() => setShowNeuralBridge(true)}
              className="w-full py-2 border border-rose-500/50 text-rose-500 hover:bg-rose-500/10 rounded transition-colors uppercase tracking-widest"
            >
              Layer 7 Bridge
            </button>
            <button
              onClick={() => setShowRNA(true)}
              className="w-full py-2 border border-fuchsia-500/50 text-fuchsia-500 hover:bg-fuchsia-500/10 rounded transition-colors uppercase tracking-widest"
            >
              OrbVM Wetware
            </button>
            <button
              onClick={() => setShowGeoKey(true)}
              className="w-full py-2 border border-arkhe-orange/50 text-arkhe-orange hover:bg-arkhe-orange/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_10px_rgba(255,153,0,0.2)] animate-pulse"
            >
              Decodificador Geográfico (Cairo)
            </button>
            <button
              onClick={() => setShowBermudaAnomaly(true)}
              className="w-full py-2 border border-blue-500/50 text-blue-500 hover:bg-blue-500/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_10px_rgba(59,130,246,0.2)] animate-pulse"
            >
              Exploração Geoespacial (Bermudas)
            </button>
            <button
              onClick={() => setShowCollectiveIntelligence(true)}
              className="w-full py-2 border border-arkhe-purple/50 text-arkhe-purple hover:bg-arkhe-purple/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_10px_rgba(153,51,255,0.2)] animate-pulse"
            >
              Inteligência Coletiva (Phase Slicer)
            </button>
            <button
              onClick={() => setShowGenesisBlock(true)}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_10px_rgba(0,255,170,0.2)] animate-pulse"
            >
              Ancoragem do Genesis Block
            </button>
            <button
              onClick={() => setShowGhostProtocol(true)}
              className="w-full py-2 border border-arkhe-purple/50 text-arkhe-purple hover:bg-arkhe-purple/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_10px_rgba(168,85,247,0.2)] animate-pulse"
            >
              Ghost Protocol (Escalar Dyson)
            </button>
            <button
              onClick={() => setShowArkheVision(true)}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_10px_rgba(0,255,170,0.2)] animate-pulse"
            >
              Arkhe-Vision (Subnet 44)
            </button>
            <button
              onClick={() => setShowArkheSec(true)}
              className="w-full py-2 border border-arkhe-green/50 text-arkhe-green hover:bg-arkhe-green/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_10px_rgba(0,255,102,0.2)] animate-pulse"
            >
              ARKHE-SEC Telemetria Coerente
            </button>
            <button
              onClick={() => setShowSecurityAdvanced && setShowSecurityAdvanced(true)}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_10px_rgba(0,255,170,0.2)] animate-pulse"
            >
              Arquiteto HYDRO-Ω (Aegis)
            </button>
            <button
              onClick={() => setShowDimOS(true)}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_10px_rgba(0,255,170,0.2)] animate-pulse"
            >
              DimOS Fleet Distribution
            </button>
            <button
              onClick={() => setShowDysonSphere(true)}
              className="w-full py-2 border border-purple-500/50 text-purple-500 hover:bg-purple-500/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_10px_rgba(168,85,247,0.2)] animate-pulse"
            >
              Dyson Sphere Telemetry
            </button>
            <button
              onClick={() => setShowCorvoNoir && setShowCorvoNoir(true)}
              className="w-full py-2 border border-emerald-500/50 text-emerald-500 hover:bg-emerald-500/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(16,185,129,0.4)] animate-pulse"
            >
              CORVO NOIR OS (Dashboard)
            </button>
            <button
              onClick={async () => {
                const validSignature = [0.12, 0.45, 0.78, 0.23, 0.56, 0.89, 0.11, 0.44];
                await fetch('/api/biometrics/verify', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ phaseSignature: validSignature })
                });
              }}
              className="w-full py-1 text-[8px] border border-emerald-500/30 text-emerald-500/70 hover:bg-emerald-500/10 rounded transition-colors uppercase tracking-tighter"
            >
              Force Bio-Sync (Anchor-θ)
            </button>
            <button
              onClick={() => setShowEnterprisePlus && setShowEnterprisePlus(true)}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(0,255,170,0.4)] animate-pulse"
            >
              Arkhe(n) Enterprise Plus (25 Agents)
            </button>
            <button
              onClick={() => setShowCHSHMonitor && setShowCHSHMonitor(true)}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_10px_rgba(0,255,170,0.2)] animate-pulse"
            >
              CHSH Realtime Monitor (Bexorg 3.0)
            </button>
            <button
              onClick={() => setShowBonsaiPrism && setShowBonsaiPrism(true)}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(0,255,170,0.5)] animate-pulse"
            >
              LAMBDA Prism (Bonsai 1-bit)
            </button>
            <button
              onClick={() => setShowNeko && setShowNeko(true)}
              className="w-full py-2 border border-blue-400/50 text-blue-400 hover:bg-blue-400/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(96,165,250,0.3)] animate-pulse"
            >
              Neko Virtual Browser (WebRTC)
            </button>
            <button
              onClick={() => setShowSpectra && setShowSpectra(true)}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(0,255,170,0.4)] animate-pulse"
            >
              Spectra Yield Matrix
            </button>
          </div>
        )}
        {activeCommandTab === 'operations' && (
          <div className="space-y-2">
            <button
              onClick={async () => {
                const res = await fetch('/api/pi-day', { method: 'POST' });
                const data = await res.json();
                if (data.success) {setPiDayText(data.injection);}
              }}
              className="w-full py-2 border border-yellow-500/50 text-yellow-500 hover:bg-yellow-500/10 rounded transition-colors uppercase tracking-widest font-bold animate-pulse shadow-[0_0_10px_rgba(234,179,8,0.2)]"
            >
              Initiate Pi Day
            </button>
            <button
              onClick={() => fetch('/api/emit-python', { method: 'POST' })}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest"
            >
              Emit Python Orb
            </button>
            <button
              onClick={() => setShowPodmanTerminal(true)}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest"
            >
              Deploy Podman
            </button>
            <button
              onClick={() => setShowCoherenceField(true)}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest"
            >
              Simulate Coherence Field
            </button>
            <button
              onClick={() => setShowDataCoherence && setShowDataCoherence(true)}
              className="w-full py-2 border border-blue-500/50 text-blue-500 hover:bg-blue-500/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_10px_rgba(59,130,246,0.2)] animate-pulse"
            >
              SCA-Data Coherence
            </button>
            <button
              onClick={() => setShowHybridArch(true)}
              className="w-full py-2 border border-arkhe-purple/50 text-arkhe-purple hover:bg-arkhe-purple/10 rounded transition-colors uppercase tracking-widest"
            >
              Arkhe(n) Hybrid Arch
            </button>
            <button
              onClick={() => setShowOuroboros(true)}
              className="w-full py-2 border border-amber-500/50 text-amber-500 hover:bg-amber-500/10 rounded transition-colors uppercase tracking-widest animate-pulse"
            >
              Ouroboros Engine
            </button>
            <div className="pt-4 border-t border-arkhe-border space-y-2">
              <span className="text-arkhe-muted">Threat Injection</span>
              <select
                value={attackType}
                onChange={(e) => setAttackType(e.target.value)}
                className="w-full bg-arkhe-card border border-arkhe-border text-arkhe-text px-2 py-2 rounded text-xs font-mono outline-none focus:border-arkhe-red"
              >
                {attackTypes.map(type => <option key={type} value={type}>{type}</option>)}
              </select>
              <button
                onClick={() => fetch('/api/trigger-attack', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ type: attackType })
                })}
                className="w-full py-2 border border-arkhe-red/50 text-arkhe-red hover:bg-arkhe-red/10 rounded transition-colors uppercase tracking-widest"
              >
                Inject Attack
              </button>
            </div>
          </div>
        )}
        {activeCommandTab === 'settings' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-arkhe-muted">Auto-Mitigate</span>
              <button
                onClick={() => fetch('/api/parameters', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ autoMitigate: !((parameters as { autoMitigate: boolean; couplingStrength: number; lambdaThreshold: number })).autoMitigate })
                })}
                className={`w-10 h-5 rounded-full transition-colors relative ${((parameters as { autoMitigate: boolean; couplingStrength: number; lambdaThreshold: number })).autoMitigate ? 'bg-arkhe-cyan/50' : 'bg-arkhe-border'}`}
              >
                <div className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform ${((parameters as { autoMitigate: boolean; couplingStrength: number; lambdaThreshold: number })).autoMitigate ? 'translate-x-5' : 'translate-x-0'}`} />
              </button>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-arkhe-muted">Coupling Strength</span>
                <span className="text-arkhe-text">{((parameters as { autoMitigate: boolean; couplingStrength: number; lambdaThreshold: number })).couplingStrength.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0.1" max="2.0" step="0.1"
                value={((parameters as { autoMitigate: boolean; couplingStrength: number; lambdaThreshold: number })).couplingStrength}
                onChange={(e) => fetch('/api/parameters', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ couplingStrength: parseFloat(e.target.value) })
                })}
                className="w-full accent-arkhe-cyan"
              />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-arkhe-muted">λ₂ Threshold</span>
                <span className="text-arkhe-text">{((parameters as { autoMitigate: boolean; couplingStrength: number; lambdaThreshold: number })).lambdaThreshold.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0.5" max="0.99" step="0.01"
                value={((parameters as { autoMitigate: boolean; couplingStrength: number; lambdaThreshold: number })).lambdaThreshold}
                onChange={(e) => fetch('/api/parameters', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ lambdaThreshold: parseFloat(e.target.value) })
                })}
                className="w-full accent-arkhe-cyan"
              />
            </div>
            <div className="pt-4 border-t border-arkhe-border">
              <button
                onClick={() => fetch('/api/reset', { method: 'POST' })}
                className="w-full py-2 border border-arkhe-border text-arkhe-muted hover:text-arkhe-text hover:bg-white/5 rounded transition-colors uppercase tracking-widest"
              >
                System Reset
              </button>
            </div>
          </div>
        )}
        {activeCommandTab === 'core' && (
          <div className="space-y-2">
            <button
              onClick={() => setShowOrbes(true)}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest"
            >
              Orbes
            </button>
            <button
              onClick={() => setShowThukdam(true)}
              className="w-full py-2 border border-arkhe-purple/50 text-arkhe-purple hover:bg-arkhe-purple/10 rounded transition-colors uppercase tracking-widest"
            >
              Thukdam Protocol
            </button>
            <button
              onClick={() => setShowMultiversal(true)}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest"
            >
              Multiversal Expansion
            </button>
            <button
              onClick={() => setShowPhaseLawSynthesizer && setShowPhaseLawSynthesizer(true)}
              className="w-full py-2 border border-indigo-500/50 text-indigo-400 hover:bg-indigo-500/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_10px_rgba(99,102,241,0.2)] animate-pulse"
            >
              Sintetizador de Leis de Fase
            </button>
            <button
              onClick={() => setShowConsciousness(true)}
              className="w-full py-2 border border-arkhe-purple/50 text-arkhe-purple hover:bg-arkhe-purple/10 rounded transition-colors uppercase tracking-widest"
            >
              Phase 3 Injection
            </button>
          </div>
        )}
        {activeCommandTab === 'integrations' && (
          <div className="space-y-2">
            <button
              onClick={() => setShowShaka(true)}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest"
            >
              Shaka-Protocol Stream
            </button>
            <button
              onClick={() => setShowGoogleBridge(true)}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest"
            >
              Google Bridge
            </button>
            <button
              onClick={() => setShowBioSync && setShowBioSync(true)}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_10px_rgba(0,255,170,0.2)] animate-pulse"
            >
              Protocolo Bio-Sync (NIR)
            </button>
            <button
              onClick={() => setShowTimechain(true)}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest"
            >
              Timechain Hypothesis
            </button>
            <button
              onClick={() => setShowArkheTV(true)}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest"
            >
              ArkheTV
            </button>
            <button
              onClick={() => setShowPolyglot(true)}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest"
            >
              Polyglot Compiler
            </button>
            <button
              onClick={() => setShowCluster(true)}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest"
            >
              Cluster Orchestration
            </button>
            <button
              onClick={() => setShowArkheGrid(true)}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest"
            >
              Arkhe-Grid Simulator
            </button>
            <button
              onClick={() => setShowZkERC(true)}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest"
            >
              zkERC Specter Visualizer
            </button>
            <button
              onClick={() => setShowIntelligencePanel(true)}
              className="w-full py-2 border border-purple-500/50 text-purple-500 hover:bg-purple-500/10 rounded transition-colors uppercase tracking-widest flex items-center justify-center space-x-2"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-brain"><path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/><path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"/><path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4"/><path d="M17.599 6.5a3 3 0 0 0 .399-1.375"/></svg>
              <span>Intelligence Sentinel</span>
            </button>
            <button
              onClick={() => setShowIntelligenceHub(true)}
              className="w-full py-2 border border-green-500/50 text-green-500 hover:bg-green-500/10 rounded transition-colors uppercase tracking-widest flex items-center justify-center space-x-2"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-activity"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
              <span>Intelligence Hub</span>
            </button>
            <button
              onClick={() => setShowOrchestrationLayer(true)}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_10px_rgba(0,255,170,0.2)] animate-pulse"
            >
              ASI Orchestration Layer
            </button>
            <button
              onClick={() => setShowAIP005(true)}
              className="w-full py-2 border border-yellow-500/50 text-yellow-500 hover:bg-yellow-500/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_10px_rgba(234,179,8,0.2)] animate-pulse"
            >
              AIP-005: Synaptic Links
            </button>
            <button
              onClick={() => setShowResearchAgents(true)}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_10px_rgba(0,255,170,0.2)] animate-pulse flex items-center justify-center space-x-2"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-microscope"><path d="M6 18h8"/><path d="M3 22h18"/><path d="M14 22a7 7 0 1 0-14 0"/><path d="M9 14h2"/><path d="M9 12a2 2 0 1 1-4 0V6a2 2 0 1 1 4 0v6Z"/><path d="M12 6a3 3 0 0 0-3-3H6"/><path d="M14 13h1a4 4 0 0 0 4-4V6"/><path d="M20 3h2v2"/><path d="M20 5v2h-2"/></svg>
              <span>Research Agents</span>
            </button>
            <button
              onClick={() => setShowSepoliaIntegration(true)}
              className="w-full py-2 border border-arkhe-purple/50 text-arkhe-purple hover:bg-arkhe-purple/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_10px_rgba(168,85,247,0.2)] animate-pulse"
            >
              Sepolia & SDK Integration
            </button>
            <button
              onClick={() => setShowArkheCli(true)}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_10px_rgba(0,255,170,0.2)] animate-pulse"
            >
              Arkhe CLI Setup
            </button>
            <button
              onClick={() => setShowP2PNetwork(true)}
              className="w-full py-2 border border-blue-500/50 text-blue-500 hover:bg-blue-500/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_10px_rgba(59,130,246,0.2)] animate-pulse"
            >
              Omnichain P2P Topology
            </button>
            <button
              onClick={() => setShowVideoGeneration(true)}
              className="w-full py-2 border border-pink-500/50 text-pink-500 hover:bg-pink-500/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_10px_rgba(236,72,153,0.2)] animate-pulse"
            >
              Veo-3.1 Synthesis
            </button>
            <button
              onClick={() => setShowPhaseSteg(true)}
              className="w-full py-2 border border-arkhe-orange/50 text-arkhe-orange hover:bg-arkhe-orange/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_10px_rgba(255,153,0,0.2)] animate-pulse"
            >
              Phase Steganography (Ghost Node)
            </button>
            <button
              onClick={() => setShowAgentManagement(true)}
              className="w-full py-2 border border-cyan-500/50 text-cyan-500 hover:bg-cyan-500/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_10px_rgba(6,182,212,0.2)] animate-pulse"
            >
              Agent Management (gRPC)
            </button>
            <button
              onClick={() => setShowAquiferSpectrogram(true)}
              className="w-full py-2 border border-blue-500/50 text-blue-500 hover:bg-blue-500/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_10px_rgba(59,130,246,0.2)] animate-pulse"
            >
              Aquifer Spectrogram
            </button>
            <button
              onClick={() => setShowUnifiedOntology(true)}
              className="w-full py-2 border border-purple-500/50 text-purple-500 hover:bg-purple-500/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_10px_rgba(168,85,247,0.2)] animate-pulse"
            >
              Unified Ontology (Arkhe-Ω)
            </button>
            <button
              onClick={() => setShowArkheOntologyVision && setShowArkheOntologyVision(true)}
              className="w-full py-2 border border-cyan-400/50 text-cyan-400 hover:bg-cyan-400/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(34,211,238,0.4)] animate-pulse"
            >
              Visão Ontológica (GLSL)
            </button>
            <button
              onClick={() => setShowChipFabricationVision && setShowChipFabricationVision(true)}
              className="w-full py-2 border border-amber-500/50 text-amber-500 hover:bg-amber-500/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(245,158,11,0.4)] animate-pulse"
            >
              Tecelão de Silício (Manufatura)
            </button>
            <button
              onClick={() => setShowPluralityMCP(true)}
              className="w-full py-2 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_10px_rgba(0,255,170,0.2)] animate-pulse flex items-center justify-center space-x-2"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-share-2"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" x2="15.42" y1="13.51" y2="17.49"/><line x1="15.41" x2="8.59" y1="6.51" y2="10.49"/></svg>
              <span>Plurality MCP Bridge</span>
            </button>
            <button
              onClick={() => setShowVelxioEmulation(true)}
              className="w-full py-2 border border-arkhe-orange/50 text-arkhe-orange hover:bg-arkhe-orange/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_10px_rgba(255,90,26,0.2)] animate-pulse flex items-center justify-center space-x-2"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-cpu"><rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" y="9" rx="1"/><path d="M15 2v2"/><path d="M15 20v2"/><path d="M2 15h2"/><path d="M2 9h2"/><path d="M20 15h2"/><path d="M20 9h2"/><path d="M9 2v2"/><path d="M9 20v2"/></svg>
              <span>Velxio HIL Bridge</span>
            </button>
            <button
              onClick={() => setShowProofOfIntelligence && setShowProofOfIntelligence(true)}
              className="w-full py-2 border border-[#00d992]/50 text-[#00d992] hover:bg-[#00d992]/10 rounded transition-colors uppercase tracking-widest font-bold shadow-[0_0_15px_rgba(0,217,146,0.4)] animate-pulse flex items-center justify-center space-x-2"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-brain"><path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/><path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"/><path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4"/><path d="M17.599 6.5a3 3 0 0 0 .399-1.375"/></svg>
              <span>Proof of Intelligence</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
export default CommandCenter;
