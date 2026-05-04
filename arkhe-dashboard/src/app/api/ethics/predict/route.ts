/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

import { ethicalPredictiveModel } from '@/lib/tfjs/ethical-predictive-model';
import type { EthicalMetrics, PredictionResult } from '@/types/ethics';

export async function POST(request: NextRequest) {
  try {
    const body: EthicalMetrics = await request.json();

    const prediction: PredictionResult = await ethicalPredictiveModel.predict(body);

    return NextResponse.json({
      success: true,
      data: prediction,
      timestamp: Date.now(),
    });
  } catch (error: unknown) {
    console.error('❌ Error in ethical prediction:', error);
    return NextResponse.json(
      { error: 'Prediction failed', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
