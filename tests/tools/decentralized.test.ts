/**
 * @license
 * Copyright 2026 solardev-xyz
 * SPDX-License-Identifier: Apache-2.0
 */

import assert from 'node:assert';
import {describe, it, before, after} from 'node:test';

import {
  ipfsCat,
  ipfsAdd,
  swarmDownload,
  swarmUpload,
  radListRepos,
  ensResolve,
} from '../../src/tools/decentralized.js';
import {serverHooks} from '../server.js';
import {html, withMcpContext} from '../utils.js';


describe('decentralized', () => {
  const server = serverHooks();

  // Mock global fetch
  const originalFetch = global.fetch;
  before(() => {
    global.fetch = async (url: string | URL | Request, options?: RequestInit) => {
      const urlStr = url.toString();
      if (urlStr.includes('/ipfs/Qm123')) {
        return {
          ok: true,
          text: async () => 'hello ipfs content',
        } as unknown as Response;
      }
      if (urlStr.includes('/api/v0/add')) {
        return {
          ok: true,
          json: async () => ({Name: 'file', Hash: 'QmAdded', Size: '123'}),
        } as unknown as Response;
      }
      if (urlStr.includes('/bzz/0xabc/')) {
        return {
          ok: true,
          text: async () => 'hello swarm content',
        } as unknown as Response;
      }
      if (urlStr.includes('/bzz') && options?.method === 'POST') {
        return {
          ok: true,
          json: async () => ({reference: '0xSwarmRef'}),
        } as unknown as Response;
      }
      if (urlStr.includes('/api/v1/projects')) {
        return {
          ok: true,
          json: async () => [{name: 'test-repo', id: 'z123'}],
        } as unknown as Response;
      }
      if (urlStr.includes('127.0.0.1:8545')) {
        const body = JSON.parse(options?.body as string);
        if (body.id === 1) {
           return {
             ok: true,
             json: async () => ({result: '0xResolverAddr'}),
           } as unknown as Response;
        }
        if (body.id === 2) {
           return {
             ok: true,
             json: async () => ({result: '0xContentHash'}),
           } as unknown as Response;
        }
      }
      return {ok: false, status: 404, statusText: 'Not Found'} as unknown as Response;
    };
  });

  after(() => {
    global.fetch = originalFetch;
  });

  it('verifies Decentralized protocol tools with mocked fetch', async () => {
    server.addHtmlRoute('/decentralized', html`<main>Decentralized Test</main>`);

    await withMcpContext(async (response, context) => {
      const mockArgs = {} as never;

      // ipfs_cat
      response.resetResponseLineForTesting();
      await ipfsCat(mockArgs).handler(
        {params: {cid: 'Qm123'}},
        response,
        context,
      );
      assert.ok(response.responseLines.some(line => line.includes('IPFS Content: Qm123')));
      assert.ok(response.responseLines.some(line => line.includes('hello ipfs content')));

      // ipfs_add
      response.resetResponseLineForTesting();
      await ipfsAdd(mockArgs).handler(
        {params: {content: 'hello ipfs'}},
        response,
        context,
      );
      assert.ok(response.responseLines.some(line => line.includes('Content Added to IPFS')));
      assert.ok(response.responseLines.some(line => line.includes('QmAdded')));

      // swarm_download
      response.resetResponseLineForTesting();
      await swarmDownload(mockArgs).handler(
        {params: {hash: '0xabc'}},
        response,
        context,
      );
      assert.ok(response.responseLines.some(line => line.includes('Swarm Content: 0xabc')));
      assert.ok(response.responseLines.some(line => line.includes('hello swarm content')));

      // swarm_upload
      response.resetResponseLineForTesting();
      await swarmUpload(mockArgs).handler(
        {params: {content: 'hello swarm'}},
        response,
        context,
      );
      assert.ok(response.responseLines.some(line => line.includes('Content Uploaded to Swarm')));
      assert.ok(response.responseLines.some(line => line.includes('0xSwarmRef')));

      // rad_list_repos
      response.resetResponseLineForTesting();
      await radListRepos(mockArgs).handler(
        {params: {}},
        response,
        context,
      );
      assert.ok(response.responseLines.some(line => line.includes('Radicle Repositories')));
      assert.ok(response.responseLines.some(line => line.includes('test-repo')));

      // ens_resolve
      response.resetResponseLineForTesting();
      await ensResolve(mockArgs).handler(
        {params: {domain: 'vitalik.eth'}},
        response,
        context,
      );
      assert.ok(response.responseLines.some(line => line.includes('ENS Resolution: vitalik.eth')));
      assert.ok(response.responseLines.some(line => line.includes('0xResolverAddr')));
    });
  });
});
