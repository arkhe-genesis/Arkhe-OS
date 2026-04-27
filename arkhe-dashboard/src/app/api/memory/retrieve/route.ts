/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// arkhe-dashboard/src/app/api/memory/retrieve/route.ts
import { NextResponse } from 'next/server';

import type { NextRequest } from 'next/server';
import { federatedCosmicMemory } from '@/lib/memory/federatedCosmicMemory';

export async function POST(request: NextRequest) {
  try {
    const query = await request.json();
    const results = await federatedCosmicMemory.retrieveByQuantumSimilarity(query);

    return NextResponse.json({
      success: true,
      data: {
        results: results.results.map(r => ({
          entryId: r.entry.entryId,
          quantumSimilarity: r.quantumSimilarity,
          semanticSimilarity: r.semanticSimilarity,
          entanglementScore: r.entanglementScore,
          coherenceScore: r.entry.coherenceScore,
          metadata: r.entry.metadata
        })),
        totalCandidates: results.totalCandidates,
        retrievalTime_ms: results.retrievalTime_ms
      },
      timestamp: Date.now()
    });
  } catch (error: unknown) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}

export async function GET() {
  const dashboard = federatedCosmicMemory.getMemoryDashboard();
  return NextResponse.json({ success: true, data: dashboard });
}
