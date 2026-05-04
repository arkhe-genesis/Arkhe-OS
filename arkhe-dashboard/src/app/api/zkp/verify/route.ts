/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// arkhe-dashboard/src/app/api/zkp/verify/route.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

import { postQuantumZKP } from '@/lib/zkp/post-quantum-zkp';
import type { ZKPProof } from '@/types/ethics';

export async function POST(request: NextRequest) {
  try {
    const { action, ...payload } = await request.json();

    switch (action) {
      case 'prove_keth_threshold': {
        const { kEth, threshold, privacyPreserved } = payload;
        const proof = await postQuantumZKP.proveKEthAboveThreshold(kEth, threshold, privacyPreserved);
        return NextResponse.json({ success: true, proof });
      }

      case 'verify_proof': {
        const { zkpProof, publicInputs } = payload as { zkpProof: ZKPProof; publicInputs: Record<string, unknown> };
        const isValid = await postQuantumZKP.verifyProof(zkpProof, publicInputs);
        return NextResponse.json({ success: true, isValid });
      }

      case 'get_metrics': {
        const metrics = postQuantumZKP.getZKPMetrics();
        return NextResponse.json({ success: true, metrics });
      }

      default:
        return NextResponse.json({ error: 'Unknown ZKP action' }, { status: 400 });
    }
  } catch (error) {
    console.error('❌ Error in ZKP API:', error);
    return NextResponse.json({ error: 'ZKP operation failed' }, { status: 500 });
  }
}
