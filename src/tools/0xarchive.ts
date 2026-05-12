/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import {zod} from '../third_party/index.js';

import {ToolCategory} from './categories.js';
import {defineTool} from './ToolDefinition.js';

/**
 * 0xArchive: Get current order book or snapshot at specific timestamp for Hyperliquid
 */
export const archiveHyperliquidOrderbook = defineTool(() => {
  return {
    name: '0xarchive_hyperliquid_orderbook',
    description: '0xArchive: Get current order book or snapshot at specific timestamp for Hyperliquid.',
    annotations: {
      category: ToolCategory.FINANCE,
      readOnlyHint: true,
      reasoningCost: 10,
    },
    schema: {
      symbol: zod.string().describe('Trading pair (e.g., BTC, ETH)'),
      timestamp: zod.number().optional().describe('Unix timestamp in ms for historical snapshot'),
      depth: zod.number().optional().describe('Number of price levels per side.'),
      apiKey: zod.string().optional().describe('API key for authentication'),
    },
    handler: async (request, response) => {
      const {symbol, timestamp, depth, apiKey} = request.params;

      let url = `https://api.0xarchive.io/v1/hyperliquid/orderbook/${symbol}`;
      const queryParams = new URLSearchParams();
      if (timestamp) queryParams.append('timestamp', timestamp.toString());
      if (depth) queryParams.append('depth', depth.toString());

      const queryString = queryParams.toString();
      if (queryString) url += `?${queryString}`;

      const headers: Record<string, string> = {};
      if (apiKey) headers['X-API-Key'] = apiKey;

      try {
        const res = await fetch(url, { headers });
        const data = await res.json();
        response.appendResponseLine(JSON.stringify(data, null, 2));
      } catch (error: any) {
        response.appendResponseLine(`Error: ${error.message}`);
      }
    },
  };
});

/**
 * 0xArchive: Get trade history with cursor pagination for Hyperliquid
 */
export const archiveHyperliquidTrades = defineTool(() => {
  return {
    name: '0xarchive_hyperliquid_trades',
    description: '0xArchive: Get trade history with cursor pagination for Hyperliquid.',
    annotations: {
      category: ToolCategory.FINANCE,
      readOnlyHint: true,
      reasoningCost: 10,
    },
    schema: {
      symbol: zod.string().describe('Trading pair (e.g., BTC, ETH)'),
      start: zod.number().describe('Start timestamp in ms'),
      end: zod.number().describe('End timestamp in ms'),
      cursor: zod.string().optional().describe('Cursor from previous response (next_cursor)'),
      limit: zod.number().optional().describe('Max results (default: 100, max: 1000)'),
      apiKey: zod.string().optional().describe('API key for authentication'),
    },
    handler: async (request, response) => {
      const {symbol, start, end, cursor, limit, apiKey} = request.params;

      let url = `https://api.0xarchive.io/v1/hyperliquid/trades/${symbol}`;
      const queryParams = new URLSearchParams();
      queryParams.append('start', start.toString());
      queryParams.append('end', end.toString());
      if (cursor) queryParams.append('cursor', cursor);
      if (limit) queryParams.append('limit', limit.toString());

      const queryString = queryParams.toString();
      if (queryString) url += `?${queryString}`;

      const headers: Record<string, string> = {};
      if (apiKey) headers['X-API-Key'] = apiKey;

      try {
        const res = await fetch(url, { headers });
        const data = await res.json();
        response.appendResponseLine(JSON.stringify(data, null, 2));
      } catch (error: any) {
        response.appendResponseLine(`Error: ${error.message}`);
      }
    },
  };
});

/**
 * 0xArchive: Get current open interest for a symbol for Hyperliquid
 */
export const archiveHyperliquidOpenInterestCurrent = defineTool(() => {
  return {
    name: '0xarchive_hyperliquid_openinterest_current',
    description: '0xArchive: Get current open interest for a symbol for Hyperliquid.',
    annotations: {
      category: ToolCategory.FINANCE,
      readOnlyHint: true,
      reasoningCost: 10,
    },
    schema: {
      symbol: zod.string().describe('Trading pair (e.g., BTC, ETH)'),
      apiKey: zod.string().optional().describe('API key for authentication'),
    },
    handler: async (request, response) => {
      const {symbol, apiKey} = request.params;

      let url = `https://api.0xarchive.io/v1/hyperliquid/openinterest/${symbol}/current`;

      const headers: Record<string, string> = {};
      if (apiKey) headers['X-API-Key'] = apiKey;

      try {
        const res = await fetch(url, { headers });
        const data = await res.json();
        response.appendResponseLine(JSON.stringify(data, null, 2));
      } catch (error: any) {
        response.appendResponseLine(`Error: ${error.message}`);
      }
    },
  };
});

/**
 * 0xArchive: Get current funding rate for a symbol for Hyperliquid
 */
export const archiveHyperliquidFundingCurrent = defineTool(() => {
  return {
    name: '0xarchive_hyperliquid_funding_current',
    description: '0xArchive: Get current funding rate for a symbol for Hyperliquid.',
    annotations: {
      category: ToolCategory.FINANCE,
      readOnlyHint: true,
      reasoningCost: 10,
    },
    schema: {
      symbol: zod.string().describe('Trading pair (e.g., BTC, ETH)'),
      apiKey: zod.string().optional().describe('API key for authentication'),
    },
    handler: async (request, response) => {
      const {symbol, apiKey} = request.params;

      let url = `https://api.0xarchive.io/v1/hyperliquid/funding/${symbol}/current`;

      const headers: Record<string, string> = {};
      if (apiKey) headers['X-API-Key'] = apiKey;

      try {
        const res = await fetch(url, { headers });
        const data = await res.json();
        response.appendResponseLine(JSON.stringify(data, null, 2));
      } catch (error: any) {
        response.appendResponseLine(`Error: ${error.message}`);
      }
    },
  };
});

/**
 * 0xArchive: Get a combined market summary for a symbol in a single API call for Hyperliquid
 */
export const archiveHyperliquidSummary = defineTool(() => {
  return {
    name: '0xarchive_hyperliquid_summary',
    description: '0xArchive: Get a combined market summary for a symbol in a single API call for Hyperliquid.',
    annotations: {
      category: ToolCategory.FINANCE,
      readOnlyHint: true,
      reasoningCost: 10,
    },
    schema: {
      symbol: zod.string().describe('Trading pair (e.g., BTC, ETH)'),
      apiKey: zod.string().optional().describe('API key for authentication'),
    },
    handler: async (request, response) => {
      const {symbol, apiKey} = request.params;

      let url = `https://api.0xarchive.io/v1/hyperliquid/summary/${symbol}`;

      const headers: Record<string, string> = {};
      if (apiKey) headers['X-API-Key'] = apiKey;

      try {
        const res = await fetch(url, { headers });
        const data = await res.json();
        response.appendResponseLine(JSON.stringify(data, null, 2));
      } catch (error: any) {
        response.appendResponseLine(`Error: ${error.message}`);
      }
    },
  };
});
