/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import {zod} from '../third_party/index.js';

import {ToolCategory} from './categories.js';
import {definePageTool} from './ToolDefinition.js';

export const listCookies = definePageTool({
  name: 'list_cookies',
  description: 'List cookies for the current page.',
  annotations: {
    category: ToolCategory.STORAGE,
    readOnlyHint: true,
  },
  schema: {
    urls: zod
      .array(zod.string())
      .optional()
      .describe(
        'Optional list of URLs to retrieve cookies for. If omitted, returns cookies for the current page URL.',
      ),
  },
  handler: async (request, response) => {
    const page = request.page.pptrPage;
    const cookies = await (request.params.urls
      ? page.cookies(...request.params.urls)
      : page.cookies());
    response.appendResponseLine('Cookies:');
    response.appendResponseLine('```json');
    response.appendResponseLine(JSON.stringify(cookies, null, 2));
    response.appendResponseLine('```');
  },
});

export const setCookie = definePageTool({
  name: 'set_cookie',
  description: 'Set a cookie on the current page.',
  annotations: {
    category: ToolCategory.STORAGE,
    readOnlyHint: false,
  },
  schema: {
    name: zod.string().describe('Cookie name'),
    value: zod.string().describe('Cookie value'),
    url: zod
      .string()
      .optional()
      .describe('The request-URI to associate with the setting of the cookie.'),
    domain: zod.string().optional().describe('Cookie domain'),
    path: zod.string().optional().describe('Cookie path'),
    expires: zod
      .number()
      .optional()
      .describe('Cookie expiration in seconds (Unix time)'),
    httpOnly: zod.boolean().optional().describe('HTTP only'),
    secure: zod.boolean().optional().describe('Secure'),
    sameSite: zod
      .enum(['Strict', 'Lax', 'None'])
      .optional()
      .describe('SameSite attribute'),
  },
  handler: async (request, response) => {
    const page = request.page.pptrPage;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    await page.setCookie(request.params as any);
    response.appendResponseLine(
      `Successfully set cookie "${request.params.name}"`,
    );
  },
});

export const deleteCookie = definePageTool({
  name: 'delete_cookie',
  description: 'Delete cookies by name from the current page.',
  annotations: {
    category: ToolCategory.STORAGE,
    readOnlyHint: false,
  },
  schema: {
    name: zod.string().describe('Name of the cookie to delete'),
    domain: zod.string().optional().describe('Cookie domain'),
    path: zod.string().optional().describe('Cookie path'),
  },
  handler: async (request, response) => {
    const page = request.page.pptrPage;
    await page.deleteCookie({
      name: request.params.name,
      domain: request.params.domain,
      path: request.params.path,
    });
    response.appendResponseLine(
      `Successfully deleted cookie "${request.params.name}"`,
    );
  },
});
