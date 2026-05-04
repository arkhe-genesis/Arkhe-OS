/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// arkhe-dashboard/src/app/api/quantum/train/route.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

import { federatedHomomorphicQuantum } from '@/lib/quantum/federatedHomomorphicQuantum';

export async function POST(request: NextRequest) {
  try {
    const { action, ...payload } = await request.json();

    switch (action) {
      case 'encrypt_data': {
        const encrypted = await federatedHomomorphicQuantum.encryptEthicalData(payload.data);
        return NextResponse.json({ success: true, encrypted });
      }
      case 'train_federated': {
        const result = await federatedHomomorphicQuantum.trainFederatedHomomorphicModel(payload.encryptedDatasets);
        return NextResponse.json({ success: true, result });
      }
      default:
        return NextResponse.json({ error: 'Unknown action' }, { status: 400 });
    }
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    return NextResponse.json({ success: false, error: message }, { status: 500 });
  }
}

export async function GET() {
  const dashboard = federatedHomomorphicQuantum.getHomomorphicDashboard();
  return NextResponse.json({ success: true, data: dashboard });
}
