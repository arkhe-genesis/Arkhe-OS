/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import assert from 'node:assert';
import {describe, it} from 'node:test';

import {
  aping,
  atraceroute,
  anslookup,
  anc,
  acurl,
  arkheNetworkMap,
} from '../../src/tools/arkhe_net.js';
import {serverHooks} from '../server.js';
import {html, withMcpContext} from '../utils.js';

describe('arkhe_net', () => {
  const server = serverHooks();

  it('verifies Arkhe networking tools', async () => {
    server.addHtmlRoute('/net', html`<main>Networking Test</main>`);

    await withMcpContext(async (response, context) => {
      const page = context.getSelectedPptrPage();
      await page.goto(server.getRoute('/net'));

      // aping
      response.resetResponseLineForTesting();
      await aping.handler(
        {params: {address: '127.1.0.1.0.0.0.1', count: 2}, page: context.getSelectedMcpPage()},
        response,
        context,
      );
      assert.ok(response.responseLines.some(line => line.includes('APING: 127.1.0.1.0.0.0.1')));
      assert.ok(response.responseLines.some(line => line.includes('Reply from 127.1.0.1.0.0.0.1')));
      assert.ok(response.responseLines.some(line => line.includes('λ2=')));

      // atraceroute
      response.resetResponseLineForTesting();
      await atraceroute.handler(
        {params: {address: '127.2.1.0.0.0.0.1'}, page: context.getSelectedMcpPage()},
        response,
        context,
      );
      assert.ok(response.responseLines.some(line => line.includes('ATRACEROUTE: 127.2.1.0.0.0.0.1')));
      assert.ok(response.responseLines.some(line => line.includes('Inter-sheet jump')));

      // anslookup
      response.resetResponseLineForTesting();
      await anslookup.handler(
        {params: {concept: 'Luz'}, page: context.getSelectedMcpPage()},
        response,
        context,
      );
      assert.ok(response.responseLines.some(line => line.includes('### ANSLOOKUP: Luz')));
      assert.ok(response.responseLines.some(line => line.includes('Address: 127.0.0.1.0.0.0.1')));

      // anslookup (not found)
      response.resetResponseLineForTesting();
      await anslookup.handler(
        {params: {concept: 'NonExistent'}, page: context.getSelectedMcpPage()},
        response,
        context,
      );
      assert.ok(response.responseLines.some(line => line.includes('Error: Concept not found')));

      // anc
      response.resetResponseLineForTesting();
      await anc.handler(
        {params: {address: '127.1.0.1.0.0.0.1', port: 80}, page: context.getSelectedMcpPage()},
        response,
        context,
      );
      assert.ok(response.responseLines.some(line => line.includes('### ANC: 127.1.0.1.0.0.0.1:80')));

      // acurl
      response.resetResponseLineForTesting();
      await acurl.handler(
        {params: {url: 'qhttp://Luz/api/status', verbose: true}, page: context.getSelectedMcpPage()},
        response,
        context,
      );
      assert.ok(response.responseLines.some(line => line.includes('### ACURL: qhttp://Luz/api/status')));
      assert.ok(response.responseLines.some(line => line.includes('X-Phase-Signature')));

      // arkheNetworkMap
      response.resetResponseLineForTesting();
      await arkheNetworkMap.handler(
        {params: {}, page: context.getSelectedMcpPage()},
        response,
        context,
      );
      assert.ok(response.responseLines.some(line => line.includes('### Arkhe(n) Comprehensive Diagnostic Map')));
      assert.ok(response.responseLines.some(line => line.includes('IP Addressing & Subnetting (CIDR)')));
      assert.ok(response.responseLines.some(line => line.includes('Load Balancing (L4 vs. L7)')));
      assert.ok(response.responseLines.some(line => line.includes('Troubleshooting Toolkit')));
    });
  });
});
