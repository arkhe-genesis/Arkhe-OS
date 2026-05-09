/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */




import assert from 'node:assert';
import {describe, it} from 'node:test';

import {listCookies, setCookie, deleteCookie} from '../../src/tools/storage.js';
import {serverHooks} from '../server.js';
import {html, withMcpContext} from '../utils.js';

describe('storage', () => {
  const server = serverHooks();

  it('sets, lists and deletes cookies', async () => {
    server.addHtmlRoute('/cookies', html`<main>Cookies test</main>`);

    await withMcpContext(async (response, context) => {
      const page = context.getSelectedPptrPage();
      await page.goto(server.getRoute('/cookies'));

      // Set cookie
      await setCookie.handler(
        {
          params: {
            name: 'test-cookie',
            value: 'test-value',
          },
          page: context.getSelectedMcpPage(),
        },
        response,
        context,
      );
      assert.ok(
        response.responseLines.some(line =>
          line.includes('Successfully set cookie "test-cookie"'),
        ),
      );

      // List cookies
      response.resetResponseLineForTesting();
      await listCookies.handler(
        {
          params: {},
          page: context.getSelectedMcpPage(),
        },
        response,
        context,
      );

      assert.ok(
        response.responseLines.some(line => line.includes('test-cookie')),
      );
      assert.ok(
        response.responseLines.some(line => line.includes('test-value')),
      );

      // Delete cookie
      response.resetResponseLineForTesting();
      await deleteCookie.handler(
        {
          params: {
            name: 'test-cookie',
          },
          page: context.getSelectedMcpPage(),
        },
        response,
        context,
      );
      assert.ok(
        response.responseLines.some(line =>
          line.includes('Successfully deleted cookie "test-cookie"'),
        ),
      );

      // Verify deletion
      response.resetResponseLineForTesting();
      await listCookies.handler(
        {
          params: {},
          page: context.getSelectedMcpPage(),
        },
        response,
        context,
      );
      assert.ok(
        !response.responseLines.some(line => line.includes('test-cookie')),
      );
    });
  });
});
