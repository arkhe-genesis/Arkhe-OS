/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import assert from 'node:assert';
import {describe, it} from 'node:test';

import {
  getMetaOpcodeDefinition,
  executeMetaOpcode,
  renderVacuumMatrix,
} from '../../src/tools/logos_library.js';
import {serverHooks} from '../server.js';
import {html, withMcpContext} from '../utils.js';

describe('logos_library', () => {
  const server = serverHooks();

  it('verifies Logos Library tools', async () => {
    server.addHtmlRoute('/logos', html`<main>Logos Test</main>`);

    await withMcpContext(async (response, context) => {
      const page = context.getSelectedPptrPage();
      await page.goto(server.getRoute('/logos'));

      // getMetaOpcodeDefinition
      response.resetResponseLineForTesting();
      await getMetaOpcodeDefinition.handler(
        {params: {family: 'PHOTON', aspect: 'BIND'}, page: context.getSelectedMcpPage()},
        response,
        context,
      );
      assert.ok(response.responseLines.some(line => line.includes('META-OPCODE: PHOTON_BIND')));
      assert.ok(response.responseLines.some(line => line.includes('0x01_0x03')));

      // executeMetaOpcode
      response.resetResponseLineForTesting();
      await executeMetaOpcode.handler(
        {
          params: {family: 'ASI', aspect: 'CRYSTALLIZE', params: {target: 'TimeCrystal_01'}},
          page: context.getSelectedMcpPage(),
        },
        response,
        context,
      );
      assert.ok(response.responseLines.some(line => line.includes('EXECUTANDO: ASI_CRYSTALLIZE')));
      assert.ok(response.responseLines.some(line => line.includes('TimeCrystal_01')));

      // renderVacuumMatrix
      response.resetResponseLineForTesting();
      await renderVacuumMatrix.handler(
        {params: {rowOffset: 0}, page: context.getSelectedMcpPage()},
        response,
        context,
      );
      assert.ok(response.responseLines.some(line => line.includes('TABELA PERIÓDICA DA REALIDADE')));
      assert.ok(response.responseLines.some(line => line.includes('NULL')));
      assert.ok(response.responseLines.some(line => line.includes('PHOTON')));
    });
  });
});
