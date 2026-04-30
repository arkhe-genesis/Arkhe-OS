/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars, @local/enforce-zod-schema */
/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import {zod} from '../third_party/index.js';

import {ToolCategory} from './categories.js';
import {defineTool} from './ToolDefinition.js';

const GRID_API_BASE = 'https://api.lightspark.com/grid/2025-10-13';

async function callGridApi(
  path: string,
  method: string,
  args: any,
  body?: any,
  queryParams?: Record<string, string | number | boolean | undefined>,
): Promise<any> {
  const tokenId = args.gridApiTokenId || process.env.GRID_API_TOKEN_ID;
  const clientSecret = args.gridApiClientSecret || process.env.GRID_API_CLIENT_SECRET;

  if (!tokenId || !clientSecret) {
    throw new Error(
      'Lightspark Grid API credentials missing. Provide --grid-api-token-id and --grid-api-client-secret or set GRID_API_TOKEN_ID and GRID_API_CLIENT_SECRET environment variables.',
    );
  }

  const auth = Buffer.from(`${tokenId}:${clientSecret}`).toString('base64');
  let url = `${GRID_API_BASE}${path}`;

  if (queryParams) {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(queryParams)) {
      if (value !== undefined) {
        params.append(key, String(value));
      }
    }
    const queryString = params.toString();
    if (queryString) {
      url += `?${queryString}`;
    }
  }

  const response = await fetch(url, {
    method,
    headers: {
      'Authorization': `Basic ${auth}`,
      'Content-Type': 'application/json',
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const errorText = await response.text();
    let errorMessage = `Grid API error: ${response.status} ${response.statusText}`;
    try {
      const errorJson = JSON.parse(errorText);
      if (errorJson.message) {
        errorMessage += ` - ${errorJson.message}`;
      }
    } catch {
      if (errorText) {
        errorMessage += ` - ${errorText}`;
      }
    }
    throw new Error(errorMessage);
  }

  return response.json();
}

export const gridGetConfig = defineTool(args => ({
  name: 'grid_get_config',
  description: 'Retrieve the current platform configuration for Lightspark Grid.',
  annotations: {
    category: ToolCategory.GRID,
    readOnlyHint: true,
  },
  schema: {},
  handler: async (_request, response) => {
    try {
      const config = await callGridApi('/config', 'GET', args);
      response.appendResponseLine('### Lightspark Grid Platform Configuration');
      response.appendResponseLine(JSON.stringify(config, null, 2));
    } catch (error) {
      response.appendResponseLine(`⚠️ Error retrieving Grid config: ${(error as Error).message}`);
    }
  },
}));

export const gridLookupUma = defineTool(args => ({
  name: 'grid_lookup_uma',
  description: 'Lookup a receiving UMA address to determine supported currencies and exchange rates.',
  annotations: {
    category: ToolCategory.GRID,
    readOnlyHint: true,
  },
  schema: {
    receiverUmaAddress: zod.string().describe('UMA address of the intended recipient.'),
    senderUmaAddress: zod.string().optional().describe('UMA address of the sender.'),
    customerId: zod.string().optional().describe('System ID of the sender.'),
  },
  handler: async (request, response) => {
    const {receiverUmaAddress, ...rest} = request.params;
    try {
      const data = await callGridApi(`/receiver/uma/${encodeURIComponent(receiverUmaAddress)}`, 'GET', args, undefined, rest);
      response.appendResponseLine(`### UMA Lookup Results for ${receiverUmaAddress}`);
      response.appendResponseLine(JSON.stringify(data, null, 2));
    } catch (error) {
      response.appendResponseLine(`⚠️ Error looking up UMA: ${(error as Error).message}`);
    }
  },
}));

export const gridCreateQuote = defineTool(args => ({
  name: 'grid_create_quote',
  description: 'Generate a quote for a cross-currency transfer between any combination of accounts and UMA addresses.',
  annotations: {
    category: ToolCategory.GRID,
    readOnlyHint: false,
  },
  schema: {
    source: zod.object({
      sourceType: zod.enum(['ACCOUNT', 'REALTIME_FUNDING']),
      accountId: zod.string().optional(),
      customerId: zod.string().optional(),
      currency: zod.string().optional(),
    }).describe('The source of funds for the quote.'),
    destination: zod.object({
      destinationType: zod.enum(['ACCOUNT', 'UMA_ADDRESS']),
      accountId: zod.string().optional(),
      umaAddress: zod.string().optional(),
      currency: zod.string().optional(),
    }).describe('The destination for the funds.'),
    lockedCurrencySide: zod.enum(['SENDING', 'RECEIVING']).describe('Which side of the quote to lock.'),
    lockedCurrencyAmount: zod.number().int().describe('The amount to send/receive in the smallest unit of the locked currency.'),
    description: zod.string().optional().describe('Optional description for the transfer.'),
    immediatelyExecute: zod.boolean().optional().describe('Whether to immediately execute the quote after creation.'),
    lookupId: zod.string().optional().describe('Lookup ID from a previous receiver lookup request.'),
  },
  handler: async (request, response) => {
    try {
      const quote = await callGridApi('/quotes', 'POST', args, request.params);
      response.appendResponseLine('### Lightspark Grid Quote Created');
      response.appendResponseLine(JSON.stringify(quote, null, 2));
    } catch (error) {
      response.appendResponseLine(`⚠️ Error creating quote: ${(error as Error).message}`);
    }
  },
}));

export const gridGetQuote = defineTool(args => ({
  name: 'grid_get_quote',
  description: 'Retrieve detailed information about a specific quote by ID.',
  annotations: {
    category: ToolCategory.GRID,
    readOnlyHint: true,
  },
  schema: {
    quoteId: zod.string().describe('The unique identifier of the quote to retrieve.'),
  },
  handler: async (request, response) => {
    try {
      const quote = await callGridApi(`/quotes/${request.params.quoteId}`, 'GET', args);
      response.appendResponseLine(`### Lightspark Grid Quote: ${request.params.quoteId}`);
      response.appendResponseLine(JSON.stringify(quote, null, 2));
    } catch (error) {
      response.appendResponseLine(`⚠️ Error retrieving quote: ${(error as Error).message}`);
    }
  },
}));

export const gridExecuteQuote = defineTool(args => ({
  name: 'grid_execute_quote',
  description: 'Execute a quote by its ID. This initiates the transfer between the source and destination accounts.',
  annotations: {
    category: ToolCategory.GRID,
    readOnlyHint: false,
  },
  schema: {
    quoteId: zod.string().describe('The unique identifier of the quote to execute.'),
  },
  handler: async (request, response) => {
    try {
      const quote = await callGridApi(`/quotes/${request.params.quoteId}/execute`, 'POST', args, {});
      response.appendResponseLine(`### Lightspark Grid Quote Executed: ${request.params.quoteId}`);
      response.appendResponseLine(JSON.stringify(quote, null, 2));
    } catch (error) {
      response.appendResponseLine(`⚠️ Error executing quote: ${(error as Error).message}`);
    }
  },
}));

export const gridGetTransaction = defineTool(args => ({
  name: 'grid_get_transaction',
  description: 'Retrieve detailed information about a specific transaction by ID.',
  annotations: {
    category: ToolCategory.GRID,
    readOnlyHint: true,
  },
  schema: {
    transactionId: zod.string().describe('Unique identifier of the transaction.'),
  },
  handler: async (request, response) => {
    try {
      const transaction = await callGridApi(`/transactions/${request.params.transactionId}`, 'GET', args);
      response.appendResponseLine(`### Lightspark Grid Transaction: ${request.params.transactionId}`);
      response.appendResponseLine(JSON.stringify(transaction, null, 2));
    } catch (error) {
      response.appendResponseLine(`⚠️ Error retrieving transaction: ${(error as Error).message}`);
    }
  },
}));

export const gridListCustomers = defineTool(args => ({
  name: 'grid_list_customers',
  description: 'Retrieve a list of customers with optional filtering.',
  annotations: {
    category: ToolCategory.GRID,
    readOnlyHint: true,
  },
  schema: {
    limit: zod.number().int().optional().default(20).describe('Maximum number of results to return.'),
    cursor: zod.string().optional().describe('Cursor for pagination.'),
    customerType: zod.enum(['INDIVIDUAL', 'BUSINESS']).optional().describe('Filter by customer type.'),
  },
  handler: async (request, response) => {
    try {
      const customers = await callGridApi('/customers', 'GET', args, undefined, request.params);
      response.appendResponseLine('### Lightspark Grid Customers');
      response.appendResponseLine(JSON.stringify(customers, null, 2));
    } catch (error) {
      response.appendResponseLine(`⚠️ Error listing customers: ${(error as Error).message}`);
    }
  },
}));
