/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import assert from 'node:assert';
import {describe, it, before, after} from 'node:test';

import {
  gridGetConfig,
  gridLookupUma,
  gridCreateQuote,
  gridGetQuote,
  gridExecuteQuote,
  gridGetTransaction,
  gridListCustomers,
} from '../../src/tools/grid.js';
import {withMcpContext} from '../utils.js';

describe('grid tools', () => {
  const originalFetch = global.fetch;
  const mockArgs = {
    gridApiTokenId: 'test-token',
    gridApiClientSecret: 'test-secret',
  } as any;

  before(() => {
    global.fetch = async (url: string | URL | Request, options?: RequestInit) => {
      const urlStr = url.toString();
      const auth = Buffer.from('test-token:test-secret').toString('base64');

      if (options?.headers && (options.headers as any)['Authorization'] !== `Basic ${auth}`) {
        return {
          ok: false,
          status: 401,
          statusText: 'Unauthorized',
          text: async () => JSON.stringify({message: 'Unauthorized'}),
        } as unknown as Response;
      }

      if (urlStr.includes('/config')) {
        return {
          ok: true,
          json: async () => ({umaDomain: 'test.com'}),
        } as unknown as Response;
      }

      if (urlStr.includes('/receiver/uma/')) {
        return {
          ok: true,
          json: async () => ({receivingUmaAddress: '$test@test.com'}),
        } as unknown as Response;
      }

      if (urlStr.includes('/quotes') && options?.method === 'POST') {
        return {
          ok: true,
          json: async () => ({id: 'Quote:123', status: 'PENDING'}),
        } as unknown as Response;
      }

      if (urlStr.includes('/quotes/Quote:123') && options?.method === 'GET') {
        return {
          ok: true,
          json: async () => ({id: 'Quote:123', status: 'PENDING'}),
        } as unknown as Response;
      }

      if (urlStr.includes('/quotes/Quote:123/execute') && options?.method === 'POST') {
        return {
          ok: true,
          json: async () => ({id: 'Quote:123', status: 'COMPLETED'}),
        } as unknown as Response;
      }

      if (urlStr.includes('/transactions/Tx:123')) {
        return {
          ok: true,
          json: async () => ({id: 'Tx:123', status: 'COMPLETED'}),
        } as unknown as Response;
      }

      if (urlStr.includes('/customers')) {
        return {
          ok: true,
          json: async () => ({data: [{id: 'Customer:123'}]}),
        } as unknown as Response;
      }

      return {
        ok: false,
        status: 404,
        statusText: 'Not Found',
        text: async () => 'Not Found',
      } as unknown as Response;
    };
  });

  after(() => {
    global.fetch = originalFetch;
  });

  it('verifies grid_get_config', async () => {
    await withMcpContext(async (response, context) => {
      await gridGetConfig(mockArgs).handler({params: {}} as any, response, context);
      assert.ok(response.responseLines.some(line => line.includes('### Lightspark Grid Platform Configuration')));
      assert.ok(response.responseLines.some(line => line.includes('test.com')));
    });
  });

  it('verifies grid_lookup_uma', async () => {
    await withMcpContext(async (response, context) => {
      await gridLookupUma(mockArgs).handler({params: {receiverUmaAddress: '$test@test.com'}}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('### UMA Lookup Results for $test@test.com')));
      assert.ok(response.responseLines.some(line => line.includes('$test@test.com')));
    });
  });

  it('verifies grid_create_quote', async () => {
    await withMcpContext(async (response, context) => {
      const params = {
        source: {sourceType: 'ACCOUNT', accountId: 'Acc:1'},
        destination: {destinationType: 'UMA_ADDRESS', umaAddress: '$test@test.com'},
        lockedCurrencySide: 'SENDING',
        lockedCurrencyAmount: 1000,
      } as any;
      await gridCreateQuote(mockArgs).handler({params}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('### Lightspark Grid Quote Created')));
      assert.ok(response.responseLines.some(line => line.includes('Quote:123')));
    });
  });

  it('verifies grid_get_quote', async () => {
    await withMcpContext(async (response, context) => {
      await gridGetQuote(mockArgs).handler({params: {quoteId: 'Quote:123'}}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('### Lightspark Grid Quote: Quote:123')));
      assert.ok(response.responseLines.some(line => line.includes('Quote:123')));
    });
  });

  it('verifies grid_execute_quote', async () => {
    await withMcpContext(async (response, context) => {
      await gridExecuteQuote(mockArgs).handler({params: {quoteId: 'Quote:123'}}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('### Lightspark Grid Quote Executed: Quote:123')));
      // The mock returns status: 'COMPLETED' for execution
      assert.ok(response.responseLines.some(line => line.includes('Quote:123')));
    });
  });

  it('verifies grid_get_transaction', async () => {
    await withMcpContext(async (response, context) => {
      await gridGetTransaction(mockArgs).handler({params: {transactionId: 'Tx:123'}}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('### Lightspark Grid Transaction: Tx:123')));
      assert.ok(response.responseLines.some(line => line.includes('Tx:123')));
    });
  });

  it('verifies grid_list_customers', async () => {
    await withMcpContext(async (response, context) => {
      await gridListCustomers(mockArgs).handler({params: {limit: 10}}, response, context);
      assert.ok(response.responseLines.some(line => line.includes('### Lightspark Grid Customers')));
      assert.ok(response.responseLines.some(line => line.includes('Customer:123')));
    });
  });
});
