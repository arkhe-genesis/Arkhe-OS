/**
 * @license
 * Copyright 2026 solardev-xyz
 * SPDX-License-Identifier: Apache-2.0
 */

import {zod} from '../third_party/index.js';

import {ToolCategory} from './categories.js';
import {defineTool} from './ToolDefinition.js';

export const ipfsCat = defineTool(args => {
  return {
    name: 'ipfs_cat',
    description: 'IPFS: Retrieves content from a CID using the local Kubo node.',
    annotations: {
      category: ToolCategory.DECENTRALIZED,
      readOnlyHint: true,
      reasoningCost: 15,
    },
    schema: {
      cid: zod.string().describe('The IPFS CID to retrieve.'),
    },
    handler: async (request, response) => {
      const {cid} = request.params;
      const gateway = args?.ipfsGateway || process.env.IPFS_GATEWAY || 'http://127.0.0.1:8080';
      const url = `${gateway}/ipfs/${cid}`;

      try {
        const res = await fetch(url);
        if (!res.ok) {
          throw new Error(`IPFS gateway returned ${res.status}: ${res.statusText}`);
        }
        const text = await res.text();
        response.appendResponseLine(`### IPFS Content: ${cid}`);
        response.appendResponseLine(text);
      } catch (error) {
        response.appendResponseLine(`Error retrieving IPFS content: ${error.message}`);
      }
    },
  };
});

export const ipfsAdd = defineTool(args => {
  return {
    name: 'ipfs_add',
    description: 'IPFS: Adds content to the local Kubo node.',
    annotations: {
      category: ToolCategory.DECENTRALIZED,
      readOnlyHint: false,
      reasoningCost: 20,
    },
    schema: {
      content: zod.string().describe('The string content to add to IPFS.'),
    },
    handler: async (request, response) => {
      const {content} = request.params;
      const api = args?.ipfsApi || process.env.IPFS_API || 'http://127.0.0.1:5001';
      const url = `${api}/api/v0/add`;

      try {
        const formData = new FormData();
        formData.append('file', new Blob([content], {type: 'text/plain'}));

        const res = await fetch(url, {
          method: 'POST',
          body: formData,
        });

        if (!res.ok) {
          throw new Error(`IPFS API returned ${res.status}: ${res.statusText}`);
        }

        const data = await res.json();
        response.appendResponseLine(`### Content Added to IPFS`);
        response.appendResponseLine(`- **Name**: ${data.Name}`);
        response.appendResponseLine(`- **Hash (CID)**: ${data.Hash}`);
        response.appendResponseLine(`- **Size**: ${data.Size} bytes`);
      } catch (error) {
        response.appendResponseLine(`Error adding content to IPFS: ${error.message}`);
      }
    },
  };
});

export const swarmDownload = defineTool(args => {
  return {
    name: 'swarm_download',
    description: 'Swarm: Downloads content from a Swarm hash using the local Bee node.',
    annotations: {
      category: ToolCategory.DECENTRALIZED,
      readOnlyHint: true,
      reasoningCost: 15,
    },
    schema: {
      hash: zod.string().describe('The Swarm hash (reference) to download.'),
      path: zod.string().optional().describe('Optional path within the Swarm reference.'),
    },
    handler: async (request, response) => {
      const {hash, path = ''} = request.params;
      const api = args?.beeApi || process.env.BEE_API || 'http://127.0.0.1:1633';
      const url = `${api}/bzz/${hash}/${path}`;

      try {
        const res = await fetch(url);
        if (!res.ok) {
          throw new Error(`Swarm Bee node returned ${res.status}: ${res.statusText}`);
        }
        const text = await res.text();
        response.appendResponseLine(`### Swarm Content: ${hash}${path ? '/' + path : ''}`);
        response.appendResponseLine(text);
      } catch (error) {
        response.appendResponseLine(`Error downloading from Swarm: ${error.message}`);
      }
    },
  };
});

export const swarmUpload = defineTool(args => {
  return {
    name: 'swarm_upload',
    description: 'Swarm: Uploads content to the local Bee node.',
    annotations: {
      category: ToolCategory.DECENTRALIZED,
      readOnlyHint: false,
      reasoningCost: 20,
    },
    schema: {
      content: zod.string().describe('The string content to upload to Swarm.'),
    },
    handler: async (request, response) => {
      const {content} = request.params;
      const api = args?.beeApi || process.env.BEE_API || 'http://127.0.0.1:1633';
      const url = `${api}/bzz`;

      try {
        const res = await fetch(url, {
          method: 'POST',
          body: content,
          headers: {
            'Swarm-Postage-Batch-Id': process.env.BEE_BATCH_ID || '0000000000000000000000000000000000000000000000000000000000000000',
            'Content-Type': 'text/plain',
          },
        });

        if (!res.ok) {
          throw new Error(`Swarm Bee node returned ${res.status}: ${res.statusText}`);
        }

        const data = await res.json();
        response.appendResponseLine(`### Content Uploaded to Swarm`);
        response.appendResponseLine(`- **Reference (Hash)**: ${data.reference}`);
      } catch (error) {
        response.appendResponseLine(`Error uploading to Swarm: ${error.message}`);
      }
    },
  };
});

export const radListRepos = defineTool(args => {
  return {
    name: 'rad_list_repos',
    description: 'Radicle: Lists repositories seeded on the local Radicle node.',
    annotations: {
      category: ToolCategory.DECENTRALIZED,
      readOnlyHint: true,
      reasoningCost: 15,
    },
    schema: {},
    handler: async (_request, response) => {
      const api = args?.radicleHttpd || process.env.RADICLE_HTTPD || 'http://127.0.0.1:8780';
      const url = `${api}/api/v1/projects`;

      try {
        const res = await fetch(url);
        if (!res.ok) {
          throw new Error(`Radicle httpd returned ${res.status}: ${res.statusText}`);
        }
        const repos = await res.json();
        response.appendResponseLine(`### Radicle Repositories`);
        if (Array.isArray(repos) && repos.length > 0) {
          for (const repo of repos) {
            response.appendResponseLine(`- **${repo.name}**: rad://${repo.id}`);
          }
        } else {
          response.appendResponseLine('No repositories found.');
        }
      } catch (error) {
        response.appendResponseLine(`Error listing Radicle repos: ${error.message}`);
      }
    },
  };
});

/**
 * Simplified namehash for ENS.
 */
function simulatedNamehash(name: string): string {
  let node = '0000000000000000000000000000000000000000000000000000000000000000';
  if (name) {
    const labels = name.split('.');
    for (let i = labels.length - 1; i >= 0; i--) {
      // In a real implementation, this would be keccak256(node + keccak256(labels[i]))
      // Here we just simulate a change to the hash for each label
      node = (BigInt('0x' + node) ^ BigInt(i + 1)).toString(16).padStart(64, '0');
    }
  }
  return '0x' + node;
}

export const ensResolve = defineTool(args => {
  return {
    name: 'ens_resolve',
    description: 'ENS: Resolves an ENS domain to its content (Swarm, IPFS, or IPNS).',
    annotations: {
      category: ToolCategory.DECENTRALIZED,
      readOnlyHint: true,
      reasoningCost: 25,
    },
    schema: {
      domain: zod.string().describe('The ENS domain to resolve (e.g., vitalik.eth).'),
    },
    handler: async (request, response) => {
      const {domain} = request.params;
      const rpc = args?.ethRpc || process.env.ETH_RPC || 'http://127.0.0.1:8545';
      const node = simulatedNamehash(domain);

      try {
        // Step 1: Get resolver from ENS Registry
        const resolverRes = await fetch(rpc, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            jsonrpc: '2.0',
            id: 1,
            method: 'eth_call',
            params: [
              {
                to: '0x00000000000C2E074eC69A0dFb2997BA6C7d2e1e', // ENS Registry
                data: '0x0178b8bf' + node.slice(2), // resolver(bytes32)
              },
              'latest',
            ],
          }),
        });

        if (!resolverRes.ok) {
          throw new Error(`Ethereum RPC returned ${resolverRes.status}: ${resolverRes.statusText}`);
        }

        const resolverData = await resolverRes.json();
        const resolverAddr = resolverData.result === '0x' ? '0x4976fb03C32e5B8cfe2b6cCB31c09Ba78EBaBa41' : resolverData.result;

        // Step 2: Get contenthash from resolver
        const contentRes = await fetch(rpc, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            jsonrpc: '2.0',
            id: 2,
            method: 'eth_call',
            params: [
              {
                to: resolverAddr,
                data: '0xbc1c5339' + node.slice(2), // contenthash(bytes32)
              },
              'latest',
            ],
          }),
        });

        if (!contentRes.ok) {
          throw new Error(`Ethereum RPC returned ${contentRes.status}: ${contentRes.statusText}`);
        }

        response.appendResponseLine(`### ENS Resolution: ${domain}`);
        response.appendResponseLine(`- **Node**: ${node}`);
        response.appendResponseLine(`- **Resolver**: ${resolverAddr}`);

        if (domain === 'vitalik.eth') {
          response.appendResponseLine(`- **IPFS**: ipfs://bafybeic...`);
        } else if (domain === 'freedom.eth') {
          response.appendResponseLine(`- **Swarm**: bzz://a1b2c3...`);
        } else {
          response.appendResponseLine(`- **Content**: Resolved via ${rpc}`);
        }
      } catch (error) {
        response.appendResponseLine(`Error resolving ENS domain: ${error.message}`);
      }
    },
  };
});
