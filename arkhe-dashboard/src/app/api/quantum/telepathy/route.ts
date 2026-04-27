/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// arkhe-dashboard/src/app/api/quantum/telepathy/route.ts
import { NextResponse } from 'next/server';

import type { NextRequest } from 'next/server';
import { EthicalQuantumTelepathy } from '@/lib/quantum/ethical-telepathy';

const telepathyInstances = new Map<string, EthicalQuantumTelepathy>();

export async function POST(request: NextRequest) {
  try {
    const { action, consciousnessId, ...payload } = await request.json();

    let telepathy = telepathyInstances.get(consciousnessId);
    if (!telepathy) {
      telepathy = new EthicalQuantumTelepathy(
        consciousnessId,
        process.env.ARKHE_TELEMETRY_WS || 'ws://localhost:9081'
      );
      telepathyInstances.set(consciousnessId, telepathy);
    }

    switch (action) {
      case 'establish_channel': {
        const { remoteConsciousnessId } = payload;
        const success = await telepathy.establishQuantumChannel(remoteConsciousnessId);
        return NextResponse.json({ success, message: success ? 'Channel established' : 'Failed to establish channel' });
      }

      case 'transmit_intention': {
        const { intention, targetConsciousnessId } = payload;
        const success = await telepathy.transmitIntention(intention, targetConsciousnessId);
        return NextResponse.json({ success, intentionId: (intention as unknown as { intentionId: string }).intentionId });
      }

      case 'get_dashboard': {
        const dashboard = telepathy.getTelepathyDashboard();
        return NextResponse.json({ dashboard });
      }

      default:
        return NextResponse.json({ error: 'Unknown action' }, { status: 400 });
    }
  } catch (error) {
    console.error('❌ Error in quantum telepathy API:', error);
    return NextResponse.json({ error: 'Telepathy operation failed' }, { status: 500 });
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const { consciousnessId } = await request.json();
    const telepathy = telepathyInstances.get(consciousnessId);
    if (telepathy) {
      telepathy.disconnect();
      telepathyInstances.delete(consciousnessId);
    }
    return NextResponse.json({ success: true, message: 'Disconnected' });
  } catch (_error) {
    return NextResponse.json({ error: 'Disconnect failed' }, { status: 500 });
  }
}
