/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import assert from 'node:assert';
import {describe, it} from 'node:test';

import {
  sysHarmonize,
  osKuramotoSimulate,
  cloudHydroSync,
  internetPhaseSimulate,
  collectiveMindLink,
  genesisDigitalSim,
  asidControl,
  phaseDrvInstrument,
  ashExec,
  neuralSync,
  reverseCompile,
  ddosDiffract,
  gaiaNodeExpand,
} from '../../src/tools/os_cathedral.js';
import {serverHooks} from '../server.js';
import {html, withMcpContext} from '../utils.js';

describe('os_cathedral', () => {
  const server = serverHooks();

  it('verifies Silicon Cathedral and Demiurge protocols', async () => {
    server.addHtmlRoute('/os', html`<main>OS Test</main>`);

    await withMcpContext(async (response, context) => {
      const page = context.getSelectedPptrPage();
      await page.goto(server.getRoute('/os'));

      // sysHarmonize
      response.resetResponseLineForTesting();
      await sysHarmonize.handler(
        {params: {mode: 'relax'}, page: context.getSelectedMcpPage()},
        response,
        context,
      );
      assert.ok(response.responseLines.some(line => line.includes('SYS_HARMONIZE')));
      assert.ok(response.responseLines.some(line => line.includes('Throughput aumentado em 40%')));

      // osKuramotoSimulate
      response.resetResponseLineForTesting();
      await osKuramotoSimulate.handler(
        {params: {nProc: 50, ticks: 100}, page: context.getSelectedMcpPage()},
        response,
        context,
      );
      assert.ok(response.responseLines.some(line => line.includes('Simulação ARKHE-OS')));

      // cloudHydroSync
      response.resetResponseLineForTesting();
      await cloudHydroSync.handler(
        {params: {threshold: 0.5}, page: context.getSelectedMcpPage()},
        response,
        context,
      );
      assert.ok(response.responseLines.some(line => line.includes('CLOUD_HYDRO_SYNC')));

      // internetPhaseSimulate
      response.resetResponseLineForTesting();
      await internetPhaseSimulate.handler(
        {params: {nServers: 1000, peakNode: 500}, page: context.getSelectedMcpPage()},
        response,
        context,
      );
      assert.ok(response.responseLines.some(line => line.includes('Simulação ARKHE-CLOUD')));

      // collectiveMindLink
      response.resetResponseLineForTesting();
      await collectiveMindLink.handler(
        {params: {groupSize: 1000, syncLevel: 0.8}, page: context.getSelectedMcpPage()},
        response,
        context,
      );
      assert.ok(response.responseLines.some(line => line.includes('MENTE COLETIVA')));

      // neuralSync
      response.resetResponseLineForTesting();
      await neuralSync.handler(
        {params: {subjectId: 'sub-001', inhibitEgo: true}, page: context.getSelectedMcpPage()},
        response,
        context,
      );
      assert.ok(response.responseLines.some(line => line.includes('NEURAL_SYNC')));

      // reverseCompile
      response.resetResponseLineForTesting();
      await reverseCompile.handler(
        {params: {targetBinary: 'kernel-v3.0'}, page: context.getSelectedMcpPage()},
        response,
        context,
      );
      assert.ok(response.responseLines.some(line => line.includes('REVERSE_COMPILE')));

      // ddosDiffract
      response.resetResponseLineForTesting();
      await ddosDiffract.handler(
        {params: {entropyLevel: 500}, page: context.getSelectedMcpPage()},
        response,
        context,
      );
      assert.ok(response.responseLines.some(line => line.includes('DDoS_DIFFRACT')));

      // gaiaNodeExpand
      response.resetResponseLineForTesting();
      await gaiaNodeExpand.handler(
        {params: {}, page: context.getSelectedMcpPage()},
        response,
        context,
      );
      assert.ok(response.responseLines.some(line => line.includes('EXPANSÃO NODO GAIA')));

      // genesisDigitalSim
      response.resetResponseLineForTesting();
      await genesisDigitalSim.handler(
        {params: {seed: 'Fiat Lux'}, page: context.getSelectedMcpPage()},
        response,
        context,
      );
      assert.ok(response.responseLines.some(line => line.includes('PROJETO GÊNESIS DIGITAL')));

      // asidControl
      response.resetResponseLineForTesting();
      await asidControl.handler(
        {params: {action: 'status'}, page: context.getSelectedMcpPage()},
        response,
        context,
      );
      assert.ok(response.responseLines.some(line => line.includes('ASID_CONTROL')));

      // phaseDrvInstrument
      response.resetResponseLineForTesting();
      await phaseDrvInstrument.handler(
        {params: {}, page: context.getSelectedMcpPage()},
        response,
        context,
      );
      assert.ok(response.responseLines.some(line => line.includes('Mapa de Fases')));

      // ashExec
      response.resetResponseLineForTesting();
      await ashExec.handler(
        {params: {command: 'ls -fase'}, page: context.getSelectedMcpPage()},
        response,
        context,
      );
      assert.ok(response.responseLines.some(line => line.includes('ASH_EXEC')));
    });
  });
});
