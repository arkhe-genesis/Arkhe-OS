/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import {zod} from '../third_party/index.js';

import {ToolCategory} from './categories.js';
import {definePageTool} from './ToolDefinition.js';

const RESEARCHHUB_API_BASE = 'https://www.researchhub.com/api';

/**
 * Corvo Noir Aesthetic: ResearchHub Search
 * Searches for scientific papers on ResearchHub.
 */
export const researchhubSearch = definePageTool({
  name: 'researchhub_search',
  description: 'Searches ResearchHub for scientific papers and documents.',
  annotations: {
    category: ToolCategory.NETWORK,
    readOnlyHint: true,
    reasoningCost: 5,
  },
  schema: {
    query: zod.string().describe('Search query for papers.'),
    page: zod.number().optional().default(1).describe('Page number for results.'),
  },
  handler: async (request, response) => {
    const {query, page} = request.params;
    const url = `${RESEARCHHUB_API_BASE}/search/paper/?search=${encodeURIComponent(query)}&page=${page}`;

    try {
      const fetchResponse = await fetch(url);
      if (!fetchResponse.ok) {
        throw new Error(`ResearchHub API error: ${fetchResponse.status}`);
      }
      const data: unknown = await fetchResponse.json();
      response.appendResponseLine('### ResearchHub Search Results');
      response.appendResponseLine(JSON.stringify(data, null, 2));
    } catch (error) {
      response.appendResponseLine(`⚠️ Error searching ResearchHub: ${error instanceof Error ? error.message : String(error)}`);
    }
  },
});

/**
 * Corvo Noir Aesthetic: ResearchHub Get Paper
 * Retrieves detailed information about a specific paper.
 */
export const researchhubGetPaper = definePageTool({
  name: 'researchhub_get_paper',
  description: 'Retrieves detailed information about a specific ResearchHub paper by ID.',
  annotations: {
    category: ToolCategory.NETWORK,
    readOnlyHint: true,
    reasoningCost: 3,
  },
  schema: {
    paperId: zod.number().describe('The ID of the paper to retrieve.'),
  },
  handler: async (request, response) => {
    const {paperId} = request.params;
    const url = `${RESEARCHHUB_API_BASE}/paper/${paperId}/`;

    try {
      const fetchResponse = await fetch(url);
      if (!fetchResponse.ok) {
        throw new Error(`ResearchHub API error: ${fetchResponse.status}`);
      }
      const data: unknown = await fetchResponse.json();
      response.appendResponseLine(`### ResearchHub Paper Detail: ${paperId}`);
      response.appendResponseLine(JSON.stringify(data, null, 2));
    } catch (error) {
      response.appendResponseLine(`⚠️ Error retrieving paper ${paperId}: ${error instanceof Error ? error.message : String(error)}`);
    }
  },
});

/**
 * Corvo Noir Aesthetic: ResearchHub Get Hubs
 * Lists scientific hubs on ResearchHub.
 */
export const researchhubGetHubs = definePageTool({
  name: 'researchhub_get_hubs',
  description: 'Retrieves a list of trending scientific hubs from ResearchHub.',
  annotations: {
    category: ToolCategory.NETWORK,
    readOnlyHint: true,
    reasoningCost: 2,
  },
  schema: {
    page: zod.number().optional().default(1).describe('Page number for results.'),
  },
  handler: async (request, response) => {
    const {page} = request.params;
    const url = `${RESEARCHHUB_API_BASE}/hub/?ordering=-paper_count,-discussion_count,id&page=${page}`;

    try {
      const fetchResponse = await fetch(url);
      if (!fetchResponse.ok) {
        throw new Error(`ResearchHub API error: ${fetchResponse.status}`);
      }
      const data: unknown = await fetchResponse.json();
      response.appendResponseLine('### ResearchHub Trending Hubs');
      response.appendResponseLine(JSON.stringify(data, null, 2));
    } catch (error) {
      response.appendResponseLine(`⚠️ Error retrieving hubs: ${error instanceof Error ? error.message : String(error)}`);
    }
  },
});
