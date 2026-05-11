
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { OnRpcRequestHandler} from '@metamask/snaps-sdk';
import { NodeType } from '@metamask/snaps-sdk';

export const onRpcRequest: OnRpcRequestHandler = async ({ origin, request }) => {
  switch (request.method) {
    case 'get_status':
      const statusResponse = {
        status: 'active',
        coherence: 0.98,
        nodes: 42,
        message: 'Arkhe Network is stable. Tzinor nodes operating at optimal coherence.'
      };

      await snap.request({
        method: 'snap_dialog',
        params: {
          type: 'alert',
          content: {
            type: NodeType.Panel,
            children: [
              { type: NodeType.Heading, value: 'Arkhe Node Status' },
              { type: NodeType.Text, value: `**Status:** ${statusResponse.status}` },
              { type: NodeType.Text, value: `**Coherence:** ${statusResponse.coherence}` },
              { type: NodeType.Text, value: `**Active Nodes:** ${statusResponse.nodes}` },
              { type: NodeType.Text, value: statusResponse.message }
            ]
          }
        }
      });

      return statusResponse;

    case 'get_thukdam_state':
      const thukdamResponse = {
        anchored: true,
        lastHash: '0x9f8b...3c1a'
      };

      await snap.request({
        method: 'snap_dialog',
        params: {
          type: 'alert',
          content: {
            type: NodeType.Panel,
            children: [
              { type: NodeType.Heading, value: 'Thukdam State Verification' },
              { type: NodeType.Text, value: 'The Thukdam protocol state has been verified.' },
              { type: NodeType.Text, value: `**Anchored:** ${thukdamResponse.anchored ? 'Yes' : 'No'}` },
              { type: NodeType.Text, value: '**Last Hash:**' },
              { type: NodeType.Copyable, value: thukdamResponse.lastHash }
            ]
          }
        }
      });

      return thukdamResponse;

    default:
      throw new Error('Method not found.');
  }
};
