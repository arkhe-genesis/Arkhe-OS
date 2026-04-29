
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// arkhe-dashboard/src/app/api/training/route.ts
import type { NextRequest} from 'next/server';
import { NextResponse } from 'next/server';

import { ethicalPredictiveModel } from '@/lib/tfjs/ethical-predictive-model';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { historicalData } = body;

    if (!historicalData || !historicalData.features || !historicalData.labels) {
      return NextResponse.json(
        { status: 'error', message: 'historicalData with features and labels is required' },
        { status: 400 }
      );
    }

    await ethicalPredictiveModel.train(historicalData, {
        epochs: 10,
        batchSize: 32,
        validationSplit: 0.2
    });

    const history = ethicalPredictiveModel.getTrainingHistory();
    const lastEpoch = history[history.length - 1];

    return NextResponse.json({
      status: 'success',
      data: {
        finalLoss: lastEpoch?.loss || 0,
        finalValLoss: lastEpoch?.valLoss || 0,
        epochs: history.length,
      },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return NextResponse.json({status: 'error', message}, {status: 500});
  }
}
