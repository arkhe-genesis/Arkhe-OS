/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// arkhe-dashboard/src/app/api/simulate/route.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

import { ethicalSimulator } from '@/lib/simulator/ethicalSimulator';

export async function POST(request: NextRequest) {
  try {
    const { scenario, baseMetrics } = await request.json();
    const result = await ethicalSimulator.simulate(scenario, baseMetrics);
    return NextResponse.json({ success: true, result });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    return NextResponse.json({ success: false, error: message }, { status: 500 });
  }
}
