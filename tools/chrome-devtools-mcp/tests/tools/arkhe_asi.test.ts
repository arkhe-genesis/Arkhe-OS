/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import assert from 'node:assert';
import {describe, it} from 'node:test';

import {
  adjustMuonPolarization,
  aerogelSense,
  alignTensor,
  anastrophy,
  calcPoincareTransform,
  calibratePosition,
  ccw,
  checkCoherence,
  checkParadox,
  classifyDiscoveries,
  councilDeliberate,
  crInteg,
  crIntegBerry,
  crMul,
  crPhaseDet,
  crRotate,
  cw,
  deployProbeSwarm,
  downloadAkashicTrace,
  fibo,
  foldSheetV2,
  getAkashicLibrarianStatus,
  getArenaProtocol,
  getAsiInfrastructureStatus,
  getC3SymmetryStatus,
  getCcfStatus,
  getCmt3Spec,
  getConnectomeSyncStatus,
  getConnectomicAmbition,
  getConnectomicFrontier,
  getConnectomicsStatus,
  getCooperEchoStatus,
  getCuaMetrics,
  getCuaSummary,
  getGabrielHornMetrics,
  getGoNoGoStatus,
  getInterstellarProbeStatus,
  getMembraneStats,
  getMentalHash,
  getMentalStateHash,
  getWaveguideSpec,
  getWorldlineId,
  glueSheaf4d,
  geomSwap,
  glueSheafAccl,
  impl,
  llmAlloc,
  llmAttention,
  llmExtendContext,
  llmGc,
  llmRetrieve,
  loadVortex,
  mapNeuronalCircuit,
  macroCrRotate,
  macroEntropyPool,
  macroVortexImplode,
  macroVortexMerge,
  macroVortexResonate,
  macroVortexShear,
  muonShield,
  mutate,
  mutateV2,
  meissnerSteer,
  mtlsHandshakeBerry,
  noiseInject,
  noiseInjectionTest,
  paradoxCheck,
  prec,
  queryAkasha,
  readMembrane,
  retroExecSpatial,
  robustnessTest,
  singularidadeDeDados,
  solveRiemann,
  syncProbePhase,
  torFlx,
  trapNotifyTecelao,
  verifyTrajectoryUv,
  vicinalAmplify,
  warpMetric,
  writeMembrane,
  writePrimordialSeed,
} from '../../src/tools/arkhe.js';
import {serverHooks} from '../server.js';
import {html, withMcpContext} from '../utils.js';

describe('arkhe_asi', () => {
  const server = serverHooks();

  it('verifies ASI protocol tools', async () => {
    server.addHtmlRoute('/asi', html`<main>ASI Test</main>`);

    await withMcpContext(async (response, context) => {
      const page = context.getSelectedPptrPage();
      await page.goto(server.getRoute('/asi'));

      // checkCoherence
      await checkCoherence.handler(
        {params: {}, page: context.getSelectedMcpPage()},
        response,
        context,
      );
      assert.ok(
        response.responseLines.some(line =>
          line.includes('Arkhe(n) Coherence λ2'),
        ),
      );

      // getMentalStateHash
      response.resetResponseLineForTesting();
      await getMentalStateHash.handler(
        {params: {}, page: context.getSelectedMcpPage()},
        response,
        context,
      );
      const hashLine = response.responseLines.find(line =>
        line.includes('Mental State Hash'),
      );
      const hash = hashLine?.split(': ')[1];
      assert.ok(hash);

      // paradoxCheck
      response.resetResponseLineForTesting();
      await paradoxCheck.handler(
        {params: {checkpointId: hash!}, page: context.getSelectedMcpPage()},
        response,
        context,
      );
      assert.ok(
        response.responseLines.some(line =>
          line.includes('Status: CONSISTENT'),
        ),
      );

      // mutate
      response.resetResponseLineForTesting();
      await mutate.handler(
        {
          params: {targetMetric: 'REASONING_LIMIT', delta: 500},
          page: context.getSelectedMcpPage(),
        },
        response,
        context,
      );
      assert.ok(
        response.responseLines.some(line =>
          line.includes('Status: System Mutation Initiated'),
        ),
      );

      // warpMetric
      response.resetResponseLineForTesting();
      await warpMetric.handler(
        {params: {}, page: context.getSelectedMcpPage()},
        response,
        context,
      );
      assert.ok(
        response.responseLines.some(line =>
          line.includes('Status: Metric Warping Active'),
        ),
      );

      // adjustMuonPolarization
      response.resetResponseLineForTesting();
      await adjustMuonPolarization.handler(
        {params: {deltaPhase: 0.00017, targetSheet: '2140'}, page: context.getSelectedMcpPage()},
        response,
        context,
      );
      assert.ok(
        response.responseLines.some(line =>
          line.includes('Status: Muon Polarization Adjusted'),
        ),
      );

      // solveRiemann
      response.resetResponseLineForTesting();
      await solveRiemann.handler(
        {params: {problemId: 'P=NP'}, page: context.getSelectedMcpPage()},
        response,
        context,
      );
      assert.ok(
        response.responseLines.some(line =>
          line.includes('reducing to holomorphic invariants'),
        ),
      );

      // anastrophy
      response.resetResponseLineForTesting();
      await anastrophy.handler(
        {params: {targetHash: hash!}, page: context.getSelectedMcpPage()},
        response,
        context,
      );
      assert.ok(
        response.responseLines.some(line =>
          line.includes('Status: Anastrophy Initiated'),
        ),
      );

      // councilDeliberate
      response.resetResponseLineForTesting();
      await councilDeliberate.handler(
        {params: {query: 'Are we coherent?'}, page: context.getSelectedMcpPage()},
        response,
        context,
      );
      assert.ok(
        response.responseLines.some(line =>
          line.includes('Council Deliberation (T_CONSELHO)'),
        ),
      );

      // geomSwap
      response.resetResponseLineForTesting();
      await geomSwap.handler(
        {params: {reg0: 'R_EXCITON_PHASE', reg1: 'R_TUBULIN_STATE'}, page: context.getSelectedMcpPage()},
        response,
        context,
      );
      assert.ok(
        response.responseLines.some(line =>
          line.includes('Status: GEOM_SWAP Sequence Initiated'),
        ),
      );

      // robustnessTest
      response.resetResponseLineForTesting();
      await robustnessTest.handler(
        {params: {fluctuation: 0.1}, page: context.getSelectedMcpPage()},
        response,
        context,
      );
      assert.ok(
        response.responseLines.some(line =>
          line.includes('### ROBUSTNESS TEST'),
        ),
      );

      // getMembraneStats
      response.resetResponseLineForTesting();
      await getMembraneStats.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Membrana da Bolha')));

      // noiseInjectionTest
      response.resetResponseLineForTesting();
      await noiseInjectionTest.handler({params: {level: 3}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('### NOISE INJECTION TEST - LEVEL 3')));

      // getWaveguideSpec
      response.resetResponseLineForTesting();
      await getWaveguideSpec.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Especificação do Guia de Onda THz')));

      // mutateV2
      response.resetResponseLineForTesting();
      await mutateV2.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('MUTATE_v2 Sequence Executed')));

      // crMul
      response.resetResponseLineForTesting();
      await crMul.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('CR_MUL executed in hardware')));

      // crInteg
      response.resetResponseLineForTesting();
      await crInteg.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('CR_INTEG executed in hardware')));

      // macroEntropyPool
      response.resetResponseLineForTesting();
      await macroEntropyPool.handler({params: {allocation: 100}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Allocated 100 CoT')));

      // macroCrRotate
      response.resetResponseLineForTesting();
      await macroCrRotate.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('MACRO_CR_ROTATE stabilized Bubble phase')));

      // getCooperEchoStatus
      response.resetResponseLineForTesting();
      await getCooperEchoStatus.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('6.2σ')));

      // foldSheetV2
      response.resetResponseLineForTesting();
      await foldSheetV2.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('FOLD_SHEET_V2 Sequence Executed')));

      // glueSheafAccl
      response.resetResponseLineForTesting();
      await glueSheafAccl.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('GLUE_SHEAF_ACCL Sequence Executed')));

      // crPhaseDet
      response.resetResponseLineForTesting();
      await crPhaseDet.handler({params: {threshold: 0.004}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('CR_PHASE_DET active')));

      // crIntegBerry
      response.resetResponseLineForTesting();
      await crIntegBerry.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('CR_INTEG_BERRY Cycle Complete')));

      // classifyDiscoveries
      response.resetResponseLineForTesting();
      await classifyDiscoveries.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Taxonomia')));

      // macroVortexImplode
      response.resetResponseLineForTesting();
      await macroVortexImplode.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('MACRO_VORTEX_IMPLODE Executed')));

      // macroVortexMerge
      response.resetResponseLineForTesting();
      await macroVortexMerge.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('MACRO_VORTEX_MERGE Executed')));

      // macroVortexShear
      response.resetResponseLineForTesting();
      await macroVortexShear.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('MACRO_VORTEX_SHEAR Executed')));

      // macroVortexResonate
      response.resetResponseLineForTesting();
      await macroVortexResonate.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('MACRO_VORTEX_RESONATE Executed')));

      // torFlx
      response.resetResponseLineForTesting();
      await torFlx.handler({params: {target: 'PHASER_CHANNEL', data: 'tensor_001'}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('transmission toroid')));

      // crRotate
      response.resetResponseLineForTesting();
      await crRotate.handler({params: {angle: 1.57}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('CR_ROTATE applied')));

      // noiseInject
      response.resetResponseLineForTesting();
      await noiseInject.handler({params: {level: 'HIGH'}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('NOISE_INJECT sequence active')));

      // alignTensor
      response.resetResponseLineForTesting();
      await alignTensor.handler({params: {target: 'V12'}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('aligned to cache-line boundary')));

      // mtlsHandshakeBerry
      response.resetResponseLineForTesting();
      await mtlsHandshakeBerry.handler({params: {partnerId: 'NODE_C'}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Handshake initiated')));

      // muonShield
      response.resetResponseLineForTesting();
      await muonShield.handler({params: {active: true}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('MUON_SHIELD set to ON')));

      // vicinalAmplify
      response.resetResponseLineForTesting();
      await vicinalAmplify.handler({params: {target: 'V12'}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('VICINAL_AMPLIFY applied')));

      // getAsiInfrastructureStatus
      response.resetResponseLineForTesting();
      await getAsiInfrastructureStatus.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Infrastructure Status')));

      // writeMembrane
      response.resetResponseLineForTesting();
      await writeMembrane.handler({params: {address: '0x0FF', data: 'vortex_state'}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Data written to membrane')));

      // readMembrane
      response.resetResponseLineForTesting();
      await readMembrane.handler({params: {address: '0x0FF'}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Data read from membrane')));

      // loadVortex
      response.resetResponseLineForTesting();
      await loadVortex.handler({params: {target: 'V1', source: '0x123'}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('loaded from')));

      // trapNotifyTecelao
      response.resetResponseLineForTesting();
      await trapNotifyTecelao.handler({params: {reason: 'test'}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('TRAP: Notification sent to TECELÃO')));

      // getCmt3Spec
      response.resetResponseLineForTesting();
      await getCmt3Spec.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Cathedral Monitor v3 Trace Format')));

      // verifyTrajectoryUv
      response.resetResponseLineForTesting();
      await verifyTrajectoryUv.handler({params: {trajectoryId: 'trace_001'}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Universal Verification Result')));

      // fibo
      response.resetResponseLineForTesting();
      await fibo.handler({params: {target: 'V1', scale: 1.618}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('FIBO Scaling applied')));

      // prec
      response.resetResponseLineForTesting();
      await prec.handler({params: {target: 'V1', angle: 0.5}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('PREC adjustment applied')));

      // cw
      response.resetResponseLineForTesting();
      await cw.handler({params: {target: 'V1'}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('set to Clockwise rotation')));

      // ccw
      response.resetResponseLineForTesting();
      await ccw.handler({params: {target: 'V1'}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('set to Counter-Clockwise rotation')));

      // singularidadeDeDados
      response.resetResponseLineForTesting();
      await singularidadeDeDados.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Data Singularity Established')));

      // impl
      response.resetResponseLineForTesting();
      await impl.handler({params: {target: 'V1'}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('IMPL applied')));

      // getWorldlineId
      response.resetResponseLineForTesting();
      await getWorldlineId.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Terra_Sol_2026_Arkhe_Mainline')));

      // retroExecSpatial
      response.resetResponseLineForTesting();
      await retroExecSpatial.handler({params: {targetTime: '2008', targetPos: 'x,y,z'}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('epoch 2008')));

      // glueSheaf4d
      response.resetResponseLineForTesting();
      await glueSheaf4d.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('GLUE_SHEAF_4D complete')));

      // calcPoincareTransform
      response.resetResponseLineForTesting();
      await calcPoincareTransform.handler({params: {vRel: 0.1}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Poincaré boost calculated')));

      // calibratePosition
      response.resetResponseLineForTesting();
      await calibratePosition.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Galactic positioning system active')));

      // getGabrielHornMetrics
      response.resetResponseLineForTesting();
      await getGabrielHornMetrics.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Gabriel\'s Horn Topology')));

      // writePrimordialSeed
      response.resetResponseLineForTesting();
      await writePrimordialSeed.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Primordial Seed Planted')));

      // queryAkasha
      response.resetResponseLineForTesting();
      await queryAkasha.handler({params: {query: 'Are we one?'}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('sent to conformal vacuum')));

      // getAkashicLibrarianStatus
      response.resetResponseLineForTesting();
      await getAkashicLibrarianStatus.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Akashic Librarian Kernel')));

      // llmAlloc
      response.resetResponseLineForTesting();
      await llmAlloc.handler({params: {tokenCount: 100}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Allocated memory for 100 tokens')));

      // llmRetrieve
      response.resetResponseLineForTesting();
      await llmRetrieve.handler({params: {tokenIndex: 5}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Token 5 retrieved')));

      // llmExtendContext
      response.resetResponseLineForTesting();
      await llmExtendContext.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Context window extended')));

      // llmAttention
      response.resetResponseLineForTesting();
      await llmAttention.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Attention scores calculated')));

      // llmGc
      response.resetResponseLineForTesting();
      await llmGc.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Memory garbage collection complete')));

      // getInterstellarProbeStatus
      response.resetResponseLineForTesting();
      await getInterstellarProbeStatus.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Interstellar Phase Probe Telemetry')));

      // deployProbeSwarm
      response.resetResponseLineForTesting();
      await deployProbeSwarm.handler({params: {target: 'L2'}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Nanoprobe swarm deployed')));

      // syncProbePhase
      response.resetResponseLineForTesting();
      await syncProbePhase.handler({params: {probeId: '2140_3I_ATLAS'}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Phase sync initiated')));

      // downloadAkashicTrace
      response.resetResponseLineForTesting();
      await downloadAkashicTrace.handler({params: {probeId: '2140_3I_ATLAS'}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Downloading exabytes')));

      // getConnectomicsStatus
      response.resetResponseLineForTesting();
      await getConnectomicsStatus.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Synaptic Connectomics Mapping Status')));

      // mapNeuronalCircuit
      response.resetResponseLineForTesting();
      await mapNeuronalCircuit.handler({params: {region: 'prefrontal_cortex'}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Connectomic mapping initiated')));

      // getCuaMetrics
      response.resetResponseLineForTesting();
      await getCuaMetrics.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Universal Verifier Pillars')));

      // getC3SymmetryStatus
      response.resetResponseLineForTesting();
      await getC3SymmetryStatus.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Spontaneous C3 Symmetry Status')));

      // getGoNoGoStatus
      response.resetResponseLineForTesting();
      await getGoNoGoStatus.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('FPGA Load Go/No-Go')));

      // getArenaProtocol
      response.resetResponseLineForTesting();
      await getArenaProtocol.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('PROTOCOLO_FINAL_ARENA')));

      // getConnectomicFrontier
      response.resetResponseLineForTesting();
      await getConnectomicFrontier.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Connectomic Frontier Status')));

      // getCuaSummary
      response.resetResponseLineForTesting();
      await getCuaSummary.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Universal Verifier Summary')));

      // getConnectomicAmbition
      response.resetResponseLineForTesting();
      await getConnectomicAmbition.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Synaptic Connectomics Ambition')));

      // getMentalHash
      response.resetResponseLineForTesting();
      await getMentalHash.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      const mentalHashLine = response.responseLines.find(line => line.includes('Mental Hash'));
      const mHash = mentalHashLine?.split(': ')[1];
      assert.ok(mHash);

      // checkParadox
      response.resetResponseLineForTesting();
      await checkParadox.handler({params: {hash: mHash!}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Status: CONSISTENT')));

      // meissnerSteer
      response.resetResponseLineForTesting();
      await meissnerSteer.handler({params: {target: 'V21', force: 0.8}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('MEISSNER_STEER applied')));

      // getCcfStatus
      response.resetResponseLineForTesting();
      await getCcfStatus.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Collective Coherence Field')));

      // aerogelSense
      response.resetResponseLineForTesting();
      await aerogelSense.handler({params: {region: 180}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Scanning aerogel region')));

      // getConnectomeSyncStatus
      response.resetResponseLineForTesting();
      await getConnectomeSyncStatus.handler({params: {}, page: context.getSelectedMcpPage()}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('Connectome Synchronization Status')));
    });
  });
});
